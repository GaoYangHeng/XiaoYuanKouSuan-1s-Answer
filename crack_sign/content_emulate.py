import struct
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from unicorn import *
from unicorn.arm_const import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libContentEncoder.so"
SAMPLE = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\samples\match_742.bin"

BASE = 0x0
STACK_ADDR = 0x6f000000
STACK_SIZE = 0x200000
HEAP_ADDR = 0x80000000
HEAP_SIZE = 0x4000000
HOOK_ADDR = 0x90000000
JNIENV_ADDR = 0xA0000000
JNI_TABLE_ADDR = 0xA0400000

R_ARM_ABS32 = 2
R_ARM_GLOB_DAT = 21
R_ARM_JUMP_SLOT = 22
R_ARM_RELATIVE = 23

# e.c 需要的 JNI 函数偏移
JNI_OFFSETS = {
    0x2ac: "GetArrayLength",
    0x2e0: "GetByteArrayElements",
    0x2c0: "ReleaseByteArrayElements",
    0x300: "NewByteArray",
    0x340: "SetByteArrayRegion",
}


class Emulator:
    def __init__(self, sample):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.elf = ELFFile(open(SO, "rb"))
        self.hook_entries = {}
        self.next_hook = HOOK_ADDR
        self.heap_top = HEAP_ADDR + 0x1000
        self.sample = sample
        self.outputs = []   # SetByteArrayRegion dump 的输出
        self.rand_state = 1

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
        self.uc.mem_map(JNIENV_ADDR, 0x1000)
        self.uc.mem_map(JNI_TABLE_ADDR, 0x10000)

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

    def _hook_code(self, uc, address, size, user):
        addr = address & ~1
        for name, ha in self.hook_entries.items():
            if (ha & ~1) == addr:
                if name.startswith("JNI_"):
                    self._jni_hook(name[4:])
                else:
                    self._handle_external(name)
                return

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

    def _handle_external(self, name):
        uc = self.uc
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        lr = uc.reg_read(UC_ARM_REG_LR)
        ret = 0

        if name == "malloc":
            ret = self.heap_top
            self.heap_top = (self.heap_top + r0 + 0xF) & ~0xF
        elif name in ("_Znwj", "_Znaj"):   # operator new / new[]
            ret = self.heap_top
            self.heap_top = (self.heap_top + r0 + 0xF) & ~0xF
        elif name == "calloc":
            ret = self.heap_top
            n = r0 * r1
            uc.mem_write(ret, b"\x00" * n)
            self.heap_top = (self.heap_top + n + 0xF) & ~0xF
        elif name in ("free", "_ZdlPv", "_ZdaPv"):
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
            a = uc.mem_read(r0, r2)
            b = uc.mem_read(r1, r2)
            ret = 0 if a == b else (1 if a > b else -1)
        elif name in ("strlen", "__strlen_chk"):
            ret = len(self._read_cstr(r0))
        elif name == "strcmp":
            a = self._read_cstr(r0)
            b = self._read_cstr(r1)
            ret = 0 if a == b else (1 if a > b else -1)
        elif name == "memchr":
            data = uc.mem_read(r0, r2)
            i = data.find(bytes([r1 & 0xFF]))
            ret = r0 + i if i >= 0 else 0
        elif name == "srand":
            self.rand_state = r0 & 0xFFFFFFFF
            ret = 0
        elif name == "rand":
            st = self.rand_state
            st = (st * 1103515245 + 12345) & 0x7FFFFFFF
            self.rand_state = st
            ret = (st >> 16) & 0x7FFF
        elif name in ("snprintf", "vsnprintf", "__vsnprintf_chk", "swprintf"):
            ret = 0
        elif name in ("strtoul", "strtol", "strtoll", "strtoull", "strtod", "wcstoul", "wcstol"):
            ret = 0
        elif name == "abort" or name == "__assert2":
            raise RuntimeError(f"abort: {name}")
        elif name == "__stack_chk_fail":
            raise RuntimeError("stack_chk_fail")
        else:
            ret = 0

        uc.reg_write(UC_ARM_REG_R0, ret)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def _jni_hook(self, name):
        uc = self.uc
        r0 = uc.reg_read(UC_ARM_REG_R0)  # env
        r1 = uc.reg_read(UC_ARM_REG_R1)  # array
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        sp = uc.reg_read(UC_ARM_REG_SP)
        lr = uc.reg_read(UC_ARM_REG_LR)
        ret = 0

        if name == "GetArrayLength":
            ret = len(self.sample)
        elif name == "GetByteArrayElements":
            # r2 = isCopy 指针
            ret = self.in_buf
        elif name == "ReleaseByteArrayElements":
            ret = 0
        elif name == "NewByteArray":
            # r1 = len
            ret = 0xAAAA  # 假 jbyteArray
        elif name == "SetByteArrayRegion":
            # r0=env, r1=array, r2=start, r3=len, [sp]=buf
            buf = struct.unpack("<I", uc.mem_read(sp, 4))[0]
            start = r2
            ln = r3
            data = bytes(uc.mem_read(buf, ln))
            self.outputs.append((start, data))
            print(f"[SetByteArrayRegion] start={start} len={ln}")
            print(f"  hex={data[:64].hex()}")
            with open(r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\samples\decrypted.bin", "wb") as fo:
                fo.write(data)
            ret = 0
        else:
            ret = 0
        uc.reg_write(UC_ARM_REG_R0, ret)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def start(self):
        self.load()
        self.apply_relocations()

        # 输入字节数组放到堆里
        self.in_buf = self.heap_top
        self.uc.mem_write(self.in_buf, self.sample)
        self.heap_top = (self.heap_top + len(self.sample) + 0xF) & ~0xF

        # JNIEnv：*JNIEnv = JNI_TABLE_ADDR
        self.uc.mem_write(JNIENV_ADDR, struct.pack("<I", JNI_TABLE_ADDR))
        generic_ha = self._alloc_hook("JNI_unknown")
        for off in range(0, 0x400, 4):
            self.uc.mem_write(JNI_TABLE_ADDR + off, struct.pack("<I", generic_ha))
        for off, name in JNI_OFFSETS.items():
            ha = self._alloc_hook("JNI_" + name)
            self.uc.mem_write(JNI_TABLE_ADDR + off, struct.pack("<I", ha))

        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=HOOK_ADDR, end=HOOK_ADDR + 0x3000000)

        sp = STACK_ADDR + STACK_SIZE - 0x100
        self.uc.reg_write(UC_ARM_REG_SP, sp)
        self.uc.reg_write(UC_ARM_REG_R0, JNIENV_ADDR)   # env
        self.uc.reg_write(UC_ARM_REG_R1, 0x1111)        # this
        self.uc.reg_write(UC_ARM_REG_R2, 0x2222)        # jbyteArray
        self.uc.reg_write(UC_ARM_REG_LR, 0xDEADBEEF)

        try:
            self.uc.emu_start(0x129a5, 0xDEADBEEF, timeout=20 * UC_SECOND_SCALE, count=5000000)
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
        print("输出数:", len(self.outputs))


if __name__ == "__main__":
    with open(SAMPLE, "rb") as f:
        sample = f.read()
    print(f"样本 {len(sample)} 字节, head={sample[:8].hex()}")
    e = Emulator(sample)
    e.start()
