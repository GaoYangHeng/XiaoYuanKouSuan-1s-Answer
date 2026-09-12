import struct
import hashlib
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

from unicorn import *
from unicorn.arm_const import *

BASE = 0x0
STACK_ADDR = 0x6f000000
STACK_SIZE = 0x100000
HEAP_ADDR = 0x80000000
HEAP_SIZE = 0x4000000
HOOK_ADDR = 0x90000000
JNIENV_ADDR = 0x91000000
JNI_TABLE_ADDR = 0x91400000
JSTR_ADDR = 0x92000000

R_ARM_ABS32 = 2
R_ARM_GLOB_DAT = 21
R_ARM_JUMP_SLOT = 22
R_ARM_RELATIVE = 23

# JNI 函数偏移（ARM EABI 函数表，index*4，已按标准 jni.h 逐一核对修正）
JNI_OFFSETS = {
    0x18: "FindClass",
    0x7c: "GetObjectClass",
    0x80: "IsInstanceOf",
    0x84: "GetMethodID",
    0x88: "CallObjectMethod",
    0x8c: "CallObjectMethodV",
    0x178: "GetFieldID",
    0x17c: "GetObjectField",
    0x1c4: "GetStaticMethodID",
    0x1c8: "CallStaticObjectMethod",
    0x1cc: "CallStaticObjectMethodV",
    0x240: "GetStaticFieldID",
    0x244: "GetStaticObjectField",
    0x258: "GetStaticIntField",
    0x290: "GetStringLength",
    0x29c: "NewStringUTF",
    0x2a0: "GetStringUTFLength",
    0x2a4: "GetStringUTFChars",
    0x2a8: "ReleaseStringUTFChars",
    0x2ac: "GetArrayLength",
    0x2b4: "GetObjectArrayElement",
    0x2e4: "GetCharArrayElements",
}


class Emulator:
    def __init__(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.elf = ELFFile(open(SO, "rb"))
        self.hook_entries = {}
        self.next_hook = HOOK_ADDR
        self.heap_top = HEAP_ADDR + 0x1000
        self.jstr_next = JSTR_ADDR + 0x1000
        self.jstr_data = {}    # jstring_ptr -> bytes
        self.jstr_len = {}     # jstring_ptr -> len
        self.md5_inputs = []
        # 环境差异注入配置（离线枚举真机分支用，见 crack_env_matrix.py）
        self.sdk_ret = None          # GetStaticIntField 返回值（真机 SDK_INT=34）
        self.memcmp_force = None     # 强制 memcmp 返回值（None=真实比较）
        self.static_obj_bytes = None # CallStaticObjectMethod/V 返回的 jstring 内容
        self.static_field_bytes = None # GetStaticObjectField 返回的 jstring 内容
        self.final_sign = None       # NewStringUTF 捕获的最终输出
        self.time_ret = 1788059615   # time() 固定返回值（敏感性测试可改）
        self.rand_init = 1           # 未 srand 时 rand LCG 初始状态
        self.method_ids = {}         # methodID/fieldID -> (kind, name, sig)
        self.next_mid = 0x6000
        # 设备值 = APK 签名 DER hex（Signature.toChars()），见 calc_device.py
        try:
            with open(r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\device_id.txt") as _f:
                self.stub_ret = _f.read().strip().encode()
        except Exception:
            self.stub_ret = b"39c0141952095d9c"

    # ---------- 映射 ----------
    def load(self):
        for seg in self.elf.iter_segments():
            if seg['p_type'] != 'PT_LOAD':
                continue
            vaddr = seg['p_vaddr']
            map_addr = vaddr & ~0xFFF
            off = vaddr - map_addr
            size = (off + seg['p_memsz'] + 0xFFF) & ~0xFFF
            self.uc.mem_map(map_addr, size)
            data = seg.data()
            if data:
                self.uc.mem_write(vaddr, data)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(HEAP_ADDR, HEAP_SIZE)
        self.uc.mem_map(HOOK_ADDR, 0x3000000)

    def _resolve_symbols(self):
        dynsym = self.elf.get_section_by_name(".dynsym")
        self.sym_addr = {}
        for sym in dynsym.iter_symbols():
            if sym['st_value']:
                self.sym_addr[sym.name] = sym['st_value']

    def apply_relocations(self):
        self._resolve_symbols()
        dynsym = self.elf.get_section_by_name(".dynsym")
        for sec in self.elf.iter_sections():
            if not isinstance(sec, RelocationSection):
                continue
            for rel in sec.iter_relocations():
                t = rel['r_info_type']
                offset = rel['r_offset']
                sym = rel['r_info_sym']
                symname = dynsym.get_symbol(sym).name if sym != 0 else None
                if t == R_ARM_RELATIVE:
                    addend = struct.unpack("<I", self.uc.mem_read(offset, 4))[0]
                    val = (BASE + addend) & 0xFFFFFFFF
                    self.uc.mem_write(offset, struct.pack("<I", val))
                elif t in (R_ARM_GLOB_DAT, R_ARM_ABS32, R_ARM_JUMP_SLOT):
                    if symname and symname in self.sym_addr:
                        val = self.sym_addr[symname]
                    else:
                        val = self._alloc_hook(symname)
                    if t == R_ARM_ABS32:
                        addend = struct.unpack("<I", self.uc.mem_read(offset, 4))[0]
                        val = (val + addend) & 0xFFFFFFFF
                    self.uc.mem_write(offset, struct.pack("<I", val))

    def _alloc_hook(self, name):
        if name in self.hook_entries:
            return self.hook_entries[name]
        addr = self.next_hook | 1
        self.next_hook += 4
        self.hook_entries[name] = addr
        return addr

    # ---------- jstring 管理 ----------
    def _make_jstring(self, data: bytes):
        p = self.jstr_next
        self.uc.mem_write(p, data + b"\x00")
        self.jstr_next += len(data) + 16
        j = self.jstr_next
        self.jstr_data[j] = p
        self.jstr_len[j] = len(data)
        self.jstr_next += 16
        return j

    # ---------- hook 回调 ----------
    def _hook_code(self, uc, address, size, user):
        addr = address & ~1
        if addr < 0x50000:
            print(f"[trace] 0x{addr:x} SP=0x{uc.reg_read(UC_ARM_REG_SP):x}")
        # 查找 hook 条目（按地址反向映射）
        for name, ha in self.hook_entries.items():
            if (ha & ~1) == addr:
                if name not in ("rand", "malloc", "free", "__aeabi_memcpy", "memcpy", "memmove", "memset"):
                    print(f"[HOOK] {name} @0x{addr:x} r0=0x{uc.reg_read(UC_ARM_REG_R0):x} r1=0x{uc.reg_read(UC_ARM_REG_R1):x} r2=0x{uc.reg_read(UC_ARM_REG_R2):x} r3=0x{uc.reg_read(UC_ARM_REG_R3):x}")
                if name.startswith("JNI_"):
                    self._jni_hook(name[4:])
                else:
                    self._handle_external(name)
                return
        if addr == 0x43338:
            self._handle_md5()
        if addr == 0x43c04:
            self._handle_md5_hex()
        if addr == 0x44280:
            self._handle_44280()
        if addr == 0x44b86:
            # 44280 调用点返回地址（LR=0x44b87 & ~1）：此时输出 string 已写好
            self._dump_44280_ret()
        if addr == 0x41a3e:
            r0 = self.uc.reg_read(UC_ARM_REG_R0)  # 结果2 = memcmp(s2, hex1)
            r4 = self.uc.reg_read(UC_ARM_REG_R4)  # 结果1 = memcmp(s1, hex1)
            r8 = self.uc.reg_read(UC_ARM_REG_R8)  # c
            sp = self.uc.reg_read(UC_ARM_REG_SP)
            vc = struct.unpack("<i", self.uc.mem_read(sp + 0xc, 4))[0]
            v10 = struct.unpack("<i", self.uc.mem_read(sp + 0x10, 4))[0]
            print(f"[delta] 结果1={r4} 结果2={r0} c={r8} [sp+0xc]={vc} [sp+0x10]={v10}")
        if addr == 0x51248:
            # 跳过 vmov.i32 q8, #0
            self.uc.reg_write(UC_ARM_REG_PC, 0x5124c | 1)
        if addr == 0x5125c or addr == 0x51266:
            # 跳过 vst1.32 {d16,d17}, [r1]! —— 手动写 16 字节 0 并 r1+=16
            r1 = self.uc.reg_read(UC_ARM_REG_R1)
            self.uc.mem_write(r1, b"\x00" * 16)
            self.uc.reg_write(UC_ARM_REG_R1, r1 + 16)
            self.uc.reg_write(UC_ARM_REG_PC, (addr + 4) | 1)
        if addr == 0x4afc6:
            # 跳过 vmov.i32 q8, #0（NEON，Unicorn 不支持）
            self.uc.reg_write(UC_ARM_REG_PC, 0x4afca | 1)
        if addr == 0x4afd2:
            # 跳过 vst1.32 {d16,d17}, [r1]! —— 手动写 16 字节 0 并 r1+=16
            r1 = self.uc.reg_read(UC_ARM_REG_R1)
            self.uc.mem_write(r1, b"\x00" * 16)
            self.uc.reg_write(UC_ARM_REG_R1, r1 + 16)
            self.uc.reg_write(UC_ARM_REG_PC, 0x4afd6 | 1)
        if addr == 0x66b46:
            # vldr d16,[r1]; vstr d16,[r4] —— 拷贝 r1[0..8] 到 r4[0..8]
            r1 = self.uc.reg_read(UC_ARM_REG_R1)
            r4 = self.uc.reg_read(UC_ARM_REG_R4)
            self.uc.mem_write(r4, bytes(self.uc.mem_read(r1, 8)))
            self.uc.reg_write(UC_ARM_REG_PC, 0x66b4e | 1)

    def _handle_str_ctor(self):
        uc = self.uc
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        lr = uc.reg_read(UC_ARM_REG_LR)
        print(f"[str_ctor 0x51248] r0=0x{r0:x} r1=0x{r1:x} LR=0x{lr:x}")
        uc.mem_write(r0, b"\x00" * 0x48)
        uc.mem_write(r0 + 4, struct.pack("<I", 0x1002))
        uc.mem_write(r0 + 8, struct.pack("<I", 6))
        r5 = 1 if r1 == 0 else 0
        uc.mem_write(r0 + 0x10, struct.pack("<I", r5))
        uc.mem_write(r0 + 0x18, struct.pack("<I", r1))
        uc.reg_write(UC_ARM_REG_PC, lr)

    def _handle_str_ctor2(self):
        uc = self.uc
        r4 = uc.reg_read(UC_ARM_REG_R0)
        uc.mem_write(r4 + 8, b"\x00" * 0x18)
        uc.reg_write(UC_ARM_REG_PC, 0x4afd9)  # Thumb 模式跳到 0x4afd8

    def _handle_external(self, name):
        uc = self.uc
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        lr = uc.reg_read(UC_ARM_REG_LR)
        ret = 0

        if name == "malloc":
            ret = self.heap_top
            self.heap_top = (self.heap_top + r0 + 0xF) & ~0xF
        elif name in ("calloc",):
            ret = self.heap_top
            n = r0 * r1
            uc.mem_write(ret, b"\x00" * n)
            self.heap_top = (self.heap_top + n + 0xF) & ~0xF
        elif name == "free":
            ret = 0
        elif name == "realloc":
            ret = self.heap_top
            self.heap_top = (self.heap_top + r1 + 0xF) & ~0xF
        elif name in ("memcpy", "__aeabi_memcpy", "memmove", "__aeabi_memmove", "wmemcpy"):
            data = bytes(uc.mem_read(r1, r2))
            uc.mem_write(r0, data)
            ret = r0
        elif name in ("memset", "__aeabi_memset", "__aeabi_memclr", "__aeabi_memclr4", "__aeabi_memclr8", "wmemset"):
            if name in ("__aeabi_memclr", "__aeabi_memclr4", "__aeabi_memclr8"):
                uc.mem_write(r0, b"\x00" * r1)
            else:
                uc.mem_write(r0, bytes([r1 & 0xFF]) * r2)
            ret = r0
        elif name == "memcmp":
            a = bytes(uc.mem_read(r0, r2))
            b = bytes(uc.mem_read(r1, r2))
            print(f"[MEMCMP] n={r2} s1={a.hex()} s2={b.hex()} s1ascii={a} s2ascii={b}")
            if self.memcmp_force is not None:
                ret = self.memcmp_force
            else:
                ret = 0 if a == b else (1 if a > b else -1)
        elif name in ("strlen", "__strlen_chk"):
            p = r0
            data = b""
            while True:
                b = uc.mem_read(p, 1)
                if b == b"\x00":
                    break
                data += b
                p += 1
                if len(data) > 4096:
                    break
            ret = len(data)
        elif name == "strcmp":
            a = self._read_cstr(r0)
            b = self._read_cstr(r1)
            ret = 0 if a == b else (1 if a > b else -1)
        elif name == "memchr":
            data = uc.mem_read(r0, r2)
            i = data.find(bytes([r1 & 0xFF]))
            ret = r0 + i if i >= 0 else 0
        elif name == "time":
            ret = self.time_ret
        elif name == "srand":
            self.rand_state = r0 & 0xFFFFFFFF
            print(f"[srand] seed=0x{self.rand_state:x}")
            ret = 0
        elif name == "rand":
            # glibc/bionic LCG: state = state*1103515245 + 12345
            st = getattr(self, "rand_state", self.rand_init)
            st = (st * 1103515245 + 12345) & 0x7FFFFFFF
            self.rand_state = st
            ret = (st >> 16) & 0x7FFF
        elif name == "snprintf" or name == "vsnprintf" or name == "__vsnprintf_chk" or name == "__vsprintf_chk":
            # __vsnprintf_chk(dest r0, size r1, flags r2, dest_len r3, format [sp+0], va_list 按值展开 [sp+4]=__stack)
            # 实证：fmt=b'%lu'，%lu 参数=[__stack] 首字（AAPCS va_list composite 按值展开）
            sp = uc.reg_read(UC_ARM_REG_SP)
            dest = r0
            size = r1 if name != "__vsprintf_chk" else 0x10000
            out = b""
            ret = 0
            try:
                fp = struct.unpack("<I", uc.mem_read(sp + 0, 4))[0]
                fmt_s = self._read_cstr(fp)
                va0 = struct.unpack("<I", uc.mem_read(sp + 4, 4))[0]
                va_off = 0
                i = 0
                n = len(fmt_s)
                while i < n:
                    c = fmt_s[i:i+1]
                    if c != b"%":
                        out += c
                        i += 1
                        continue
                    j = i + 1
                    while j < n and fmt_s[j:j+1] in b"-+ #0123456789.*lz":
                        j += 1
                    conv = fmt_s[j:j+1]
                    if conv in (b"d", b"i", b"u"):
                        v = struct.unpack("<I", uc.mem_read(va0 + va_off, 4))[0]
                        if conv != b"u" and v >= 0x80000000:
                            v -= 0x100000000
                        out += str(v).encode()
                        va_off += 4
                    elif conv == b"x" or conv == b"X" or conv == b"p":
                        v = struct.unpack("<I", uc.mem_read(va0 + va_off, 4))[0]
                        out += b"%x" % v
                        va_off += 4
                    elif conv == b"c":
                        v = struct.unpack("<I", uc.mem_read(va0 + va_off, 4))[0]
                        out += bytes([v & 0xFF])
                        va_off += 4
                    elif conv == b"s":
                        sa = struct.unpack("<I", uc.mem_read(va0 + va_off, 4))[0]
                        out += self._read_cstr(sa)[:512]
                        va_off += 4
                    elif conv == b"%":
                        out += b"%"
                    else:
                        out += c
                    i = j + 1
                self._vsnp_count = getattr(self, "_vsnp_count", 0) + 1
                if not hasattr(self, "_vsnp_outs"):
                    self._vsnp_outs = []
                self._vsnp_outs.append(out)
                if self._vsnp_count <= 3:
                    print(f"[vsnprintf #{self._vsnp_count}] fmt={fmt_s!r} out={out[:24]!r}")
                if size > 0:
                    data = out[: size - 1]
                    uc.mem_write(dest, data + b"\x00")
                    ret = len(data)
                else:
                    ret = len(out)
            except Exception as ex:
                print(f"[vsnprintf] 模拟失败: {ex} LR=0x{lr:x}")
                ret = 0
        elif name == "abort" or name == "__assert2":
            lr = uc.reg_read(UC_ARM_REG_LR)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            print(f"[abort] LR=0x{lr:x} r0=0x{r0:x} r1=0x{r1:x} r2=0x{r2:x} r3=0x{r3:x}")
            raise RuntimeError(f"abort called: {name}")
        elif name == "__stack_chk_fail":
            raise RuntimeError("stack_chk_fail")
        else:
            # 其他函数返回 0（默认），不崩溃
            ret = 0

        uc.reg_write(UC_ARM_REG_R0, ret)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def _read_cstr(self, addr):
        if addr == 0:
            return b""
        p = addr
        data = b""
        while True:
            b = self.uc.mem_read(p, 1)
            if b == b"\x00":
                break
            data += b
            p += 1
            if len(data) > 4096:
                break
        return data

    def _handle_md5(self):
        uc = self.uc
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        lr = uc.reg_read(UC_ARM_REG_LR)
        print(f"[MD5] r0=0x{r0:x} r1=0x{r1:x} LR=0x{lr:x}")
        # 解析 std::string
        b0 = uc.mem_read(r1, 1)[0]
        if b0 & 1:
            # heap
            ln = struct.unpack("<I", uc.mem_read(r1 + 4, 4))[0]
            ptr = struct.unpack("<I", uc.mem_read(r1 + 8, 4))[0]
        else:
            ln = b0 >> 1
            ptr = r1 + 1
        data = uc.mem_read(ptr, ln) if ln else b""
        self.md5_inputs.append(data)
        print(f"[MD5] 输入({ln} 字节): {data!r}")
        print(f"[MD5] hex: {data.hex()}")
        # 用 hashlib 计算真实 MD5，写入输出结构（digest 在 r0[0x5c]，flag 在 r0[0]）
        digest = hashlib.md5(bytes(data)).digest()
        uc.mem_write(r0 + 0x5c, digest)
        uc.mem_write(r0, b"\x01")
        print(f"[MD5] 输出 digest: {digest.hex()}")
        # 跳过 MD5 函数体（含 NEON 指令，Unicorn 不支持），直接返回
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def _handle_md5_hex(self):
        uc = self.uc
        r0 = uc.reg_read(UC_ARM_REG_R0)  # 输出 string 对象
        r1 = uc.reg_read(UC_ARM_REG_R1)  # digest 结构
        lr = uc.reg_read(UC_ARM_REG_LR)
        digest = bytes(uc.mem_read(r1 + 0x5c, 16))
        hexstr = digest.hex().encode()
        ptr = self.heap_top
        uc.mem_write(ptr, hexstr)
        self.heap_top = (self.heap_top + len(hexstr) + 0xF) & ~0xF
        uc.mem_write(r0, b"\x01")
        uc.mem_write(r0 + 4, struct.pack("<I", len(hexstr)))
        uc.mem_write(r0 + 8, struct.pack("<I", ptr))
        print(f"[MD5_hex] 输出: {hexstr.decode()}")
        uc.reg_write(UC_ARM_REG_PC, lr)

    def _handle_44280(self):
        # 0x44280 自然放行执行：只记参数，不改 PC（让主函数的 bl 正常调用它）
        uc = self.uc
        r0 = uc.reg_read(UC_ARM_REG_R0)  # 输出 string 对象（sret）
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        lr = uc.reg_read(UC_ARM_REG_LR)
        print(f"[44280] 进入 r0=0x{r0:x} r1=0x{r1:x} r2={r2}(0x{r2:x}) LR=0x{lr:x}")
        for label, addr in (("r1", r1), ("r0", r0)):
            try:
                raw = bytes(uc.mem_read(addr, 32))
                print(f"    {label}[0x{addr:x}] 32B hex={raw.hex()}")
                b0 = raw[0]
                if b0 & 1:
                    ln = struct.unpack("<I", raw[4:8])[0]
                    ptr = struct.unpack("<I", raw[8:12])[0]
                    data = bytes(uc.mem_read(ptr, min(ln, 96))) if ln else b""
                    print(f"    {label} SSO-heap len={ln} ptr=0x{ptr:x} data={data!r}")
                else:
                    ln = b0 >> 1
                    data = raw[1:1 + min(ln, 12)]
                    print(f"    {label} SSO-short len={ln} data={data!r}")
            except Exception as ex:
                print(f"    {label} dump 失败: {ex}")
        # r1 对象的第 3 字段疑似堆指针：dump 堆内容与 r1 周围栈区
        try:
            hp = struct.unpack("<I", uc.mem_read(r1 + 8, 4))[0]
            heap = bytes(uc.mem_read(hp, 64))
            print(f"    r1[8]堆指针=0x{hp:x} 前64B hex={heap.hex()}")
        except Exception as ex:
            print(f"    r1[8] 堆读取失败: {ex}")
        try:
            stk = bytes(uc.mem_read(r1 - 32, 96))
            print(f"    栈[r1-32..r1+64] hex={stk.hex()}")
        except Exception as ex:
            print(f"    栈区读取失败: {ex}")
        self.out44280 = r0
        self.ret44280_lr = lr

    def _dump_44280_ret(self):
        # 0x44b87 = 44280 返回点：读输出 string（libc++ SSO 格式）
        uc = self.uc
        out = getattr(self, "out44280", None)
        if out is None:
            return
        try:
            b0 = uc.mem_read(out, 1)[0]
            if b0 & 1:
                ln = struct.unpack("<I", uc.mem_read(out + 4, 4))[0]
                ptr = struct.unpack("<I", uc.mem_read(out + 8, 4))[0]
            else:
                ln = b0 >> 1
                ptr = out + 1
            data = bytes(uc.mem_read(ptr, ln)) if ln else b""
            print(f"[44280 返回] T({ln}字节) = {data!r} hex={data.hex()}")
            self.real_T = data
        except Exception as ex:
            print(f"[44280 返回] 读取失败: {ex}")

    # ---------- JNI hook ----------
    def _mid_info(self, mid):
        return self.method_ids.get(mid, ("?", hex(mid), ""))

    def _jni_hook(self, name):
        uc = self.uc
        r0 = uc.reg_read(UC_ARM_REG_R0)  # env
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        lr = uc.reg_read(UC_ARM_REG_LR)
        ret = 0
        if name in ("GetStringUTFLength", "GetStringLength"):
            ret = self.jstr_len.get(r1, 0)
        elif name == "GetStringUTFChars":
            ret = self.jstr_data.get(r1, 0)
            print(f"[GetStringUTFChars] r1=0x{r1:x} -> {self._read_cstr(ret) if ret else b''!r}")
        elif name == "ReleaseStringUTFChars":
            ret = 0
        elif name == "FindClass":
            cn = self._read_cstr(r1)
            print(f"[FindClass] class={cn!r}")
            ret = 0x5000  # 假 jclass
        elif name in ("GetStaticMethodID", "GetMethodID"):
            mn = self._read_cstr(r2).decode(errors="replace")
            sg = self._read_cstr(r3).decode(errors="replace")
            ret = self.next_mid
            self.method_ids[ret] = ("m", mn, sg)
            self.next_mid += 0x10
            print(f"[{name}] name={mn!r} sig={sg!r} -> mid=0x{ret:x}")
        elif name in ("GetFieldID", "GetStaticFieldID"):
            fn = self._read_cstr(r2).decode(errors="replace")
            sg = self._read_cstr(r3).decode(errors="replace")
            ret = self.next_mid
            self.method_ids[ret] = ("f", fn, sg)
            self.next_mid += 0x10
            print(f"[{name}] name={fn!r} sig={sg!r} -> fid=0x{ret:x}")
        elif name == "GetObjectField":
            print(f"[GetObjectField] fid={self._mid_info(r2)}")
            ret = 0x8000  # 假 jobject
        elif name == "GetObjectClass":
            ret = 0x8000  # 假 jclass
        elif name == "CallObjectMethod":
            print(f"[CallObjectMethod] obj=0x{r1:x} mid={self._mid_info(r2)}")
            ret = 0xCCCC  # toCharArray() 返回的 char[] 句柄
        elif name == "GetObjectArrayElement":
            ret = self._make_jstring(self.stub_ret)  # array[0] = 设备ID jstring
        elif name == "GetArrayLength":
            ret = len(self.stub_ret)  # char[] 长度
        elif name == "GetCharArrayElements":
            utf16 = b"".join(bytes([b, 0]) for b in self.stub_ret)
            p = self.jstr_next
            self.uc.mem_write(p, utf16 + b"\x00\x00")
            self.jstr_next += len(utf16) + 16
            ret = p
        elif name == "GetStaticObjectField":
            print(f"[GetStaticObjectField] field={self._mid_info(r2)}")
            if self.static_field_bytes is not None:
                ret = self._make_jstring(self.static_field_bytes)
            else:
                ret = 0x8000
        elif name == "GetStaticIntField":
            print(f"[GetStaticIntField] field={self._mid_info(r2)}")
            ret = self.sdk_ret if self.sdk_ret is not None else 0
        elif name == "CallStaticObjectMethod":
            print(f"[CallStaticObjectMethod] mid={self._mid_info(r2)}")
            if self.static_obj_bytes is not None:
                ret = self._make_jstring(self.static_obj_bytes)
            else:
                ret = 0x8000  # 假对象
        elif name == "CallStaticObjectMethodV":
            print(f"[CallStaticObjectMethodV] mid={self._mid_info(r2)} args_ptr=0x{r3:x}")
            if r3:
                try:
                    args = bytes(uc.mem_read(r3, 8))
                    print(f"  args8: {args.hex()}")
                    ptr = struct.unpack("<I", args[0:4])[0]
                    if ptr in self.jstr_data:
                        print(f"  arg0 jstring -> {self._read_cstr(self.jstr_data[ptr])!r}")
                except Exception as ex:
                    print(f"  args read fail: {ex}")
            if self.static_obj_bytes is not None:
                ret = self._make_jstring(self.static_obj_bytes)
            else:
                ret = 0x8000
        elif name == "CallObjectMethodV":
            print(f"[CallObjectMethodV] obj=0x{r1:x} mid={self._mid_info(r2)} args_ptr=0x{r3:x}")
            if r3:
                try:
                    args = bytes(uc.mem_read(r3, 8))
                    print(f"  args8: {args.hex()}")
                    ptr = struct.unpack("<I", args[0:4])[0]
                    if ptr in self.jstr_data:
                        print(f"  arg0 jstring -> {self._read_cstr(self.jstr_data[ptr])!r}")
                except Exception as ex:
                    print(f"  args read fail: {ex}")
            ret = 0x8000
        elif name == "IsInstanceOf":
            ret = 1  # JNI_TRUE
        elif name == "NewStringUTF":
            s = self._read_cstr(r1)
            print(f"[NewStringUTF] 最终字符串 = {s!r}")
            self.final_sign = s.decode(errors="replace")
            ret = self._make_jstring(s)
        else:
            ret = 0
        uc.reg_write(UC_ARM_REG_R0, ret)
        uc.reg_write(UC_ARM_REG_PC, lr)

    # ---------- 启动 ----------
    def start(self, path, key, ts):
        self.load()
        self.apply_relocations()
        self.path_bytes = path.encode()
        self.key_bytes = key.encode()
        # 构造 JNIEnv：JNIEnv 指针指向函数表（*JNIEnv = JNI_TABLE_ADDR）
        self.uc.mem_write(JNIENV_ADDR, struct.pack("<I", JNI_TABLE_ADDR))
        # 未知偏移逐个分配 stub（返回 0），避免跳转到 0，且序列中可辨认具体偏移
        for off in range(0, 0x300, 4):
            if off in JNI_OFFSETS:
                continue
            ha = self._alloc_hook("JNI_unk_%x" % off)
            self.uc.mem_write(JNI_TABLE_ADDR + off, struct.pack("<I", ha))
        for off, name in JNI_OFFSETS.items():
            ha = self._alloc_hook("JNI_" + name)
            self.uc.mem_write(JNI_TABLE_ADDR + off, struct.pack("<I", ha))
        # hook 区：UC_HOOK_CODE 拦截
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=HOOK_ADDR, end=HOOK_ADDR + 0x3000000)
        # MD5 入口 hook
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=0x43338 & ~1, end=(0x43338 & ~1) | 1)
        # MD5 hex 转换 hook
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=0x43c04 & ~1, end=(0x43c04 & ~1) | 1)
        # 时间戳格式化 hook（0x44280）
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=0x44280 & ~1, end=(0x44280 & ~1) | 1)
        # 44280 返回点（LR=0x44b87）：输出 string 已写好，读 T
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=0x44b86 & ~1, end=(0x44b86 & ~1) | 1)
        # delta 计算 dump hook（0x41a3e）
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=0x41a3e & ~1, end=(0x41a3e & ~1) | 1)
        # NEON string 构造函数 hook（0x51248 vmov.i32 / 0x5125c/0x51266 vst1.32）
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=0x51248 & ~1, end=(0x51248 & ~1) | 1)
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=0x5125c & ~1, end=(0x5125c & ~1) | 1)
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=0x51266 & ~1, end=(0x51266 & ~1) | 1)
        # NEON 指令 hook（0x4afc6 vmov.i32 / 0x4afd2 vst1.32）
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=0x4afc6 & ~1, end=(0x4afc6 & ~1) | 1)
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=0x4afd2 & ~1, end=(0x4afd2 & ~1) | 1)
        # NEON string 拷贝 hook（0x66b46 vldr/vstr）
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=0x66b46 & ~1, end=(0x66b46 & ~1) | 1)
        # jstring：path 需同时注册到 env（函数第一个字符串从 r0=env 读取）
        p_path = self.jstr_next
        self.uc.mem_write(p_path, self.path_bytes + b"\x00")
        self.jstr_next += len(self.path_bytes) + 16
        path_jstr = self.jstr_next
        self.jstr_data[path_jstr] = p_path
        self.jstr_len[path_jstr] = len(self.path_bytes)
        self.jstr_next += 16
        key_jstr = self._make_jstring(self.key_bytes)
        # env 也注册为 path 句柄
        self.jstr_data[JNIENV_ADDR] = p_path
        self.jstr_len[JNIENV_ADDR] = len(self.path_bytes)
        sp = STACK_ADDR + STACK_SIZE - 0x100
        self.uc.mem_write(sp, struct.pack("<I", ts))
        self.uc.reg_write(UC_ARM_REG_SP, sp)
        self.uc.reg_write(UC_ARM_REG_R0, JNIENV_ADDR)
        self.uc.reg_write(UC_ARM_REG_R1, 0x1111)
        self.uc.reg_write(UC_ARM_REG_R2, path_jstr)  # r2 = str = path
        self.uc.reg_write(UC_ARM_REG_R3, key_jstr)   # r3 = str2 = key
        self.uc.reg_write(UC_ARM_REG_LR, 0xDEADBEEF)
        try:
            self.uc.emu_start(0x414e8 | 1, 0xDEADBEEF, timeout=8 * UC_SECOND_SCALE, count=200000)
        except UcError as e:
            pc = self.uc.reg_read(UC_ARM_REG_PC)
            lr = self.uc.reg_read(UC_ARM_REG_LR)
            sp = self.uc.reg_read(UC_ARM_REG_SP)
            r0 = self.uc.reg_read(UC_ARM_REG_R0)
            print(f"[模拟结束] UcError: {e}")
            print(f"  PC=0x{pc:x} LR=0x{lr:x} SP=0x{sp:x} R0=0x{r0:x}")
            try:
                code = self.uc.mem_read(pc & ~1, 16)
                print(f"  code @PC: {code.hex()}")
            except Exception:
                pass
        print("MD5 输入 dump 完成，共", len(self.md5_inputs), "条")


if __name__ == "__main__":
    e = Emulator()
    e.time_ret = 1788084650  # 真机样本时刻 18:10:50
    e.start("/solar-activity/android/activity/6", "wdi4n2t8edr", 1788084650)
    print("final_sign =", e.final_sign)
    print("期望       = 68637e3ae7506ac7c0328b7a146882dc")
    outs = getattr(e, "_vsnp_outs", [])
    print(f"vsnprintf 段数={len(outs)}")
    print("段列表 =", [o.decode('ascii', 'replace') for o in outs])
