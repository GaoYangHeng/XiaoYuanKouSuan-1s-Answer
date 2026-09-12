import struct
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from unicorn import *
from unicorn.arm_const import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

HEAP_ADDR = 0x80000000
HOOK_ADDR = 0x90000000
STACK_ADDR = 0x6f000000
JNIENV_ADDR = 0x91000000
JSTR_ADDR = 0x92000000

FN = 0x414e6
MD5 = 0x43338

JNI_OFFSETS = {
    0x18: "FindClass", 0x80: "IsInstanceOf", 0x84: "GetMethodID",
    0x8c: "CallObjectMethodV", 0x178: "GetFieldID", 0x17c: "jni_17c",
    0x240: "GetStaticMethodID", 0x258: "CallStaticObjectMethodA",
    0x290: "GetStringUTFLength", 0x2a4: "GetStringUTFChars", 0x2a8: "ReleaseStringUTFChars",
}

REG_NAMES = {"r8": UC_ARM_REG_R8, "sb": UC_ARM_REG_R9, "sl": UC_ARM_REG_R10, "fp": UC_ARM_REG_R11,
             "r9": UC_ARM_REG_R9, "r10": UC_ARM_REG_R10, "r11": UC_ARM_REG_R11, "ip": UC_ARM_REG_R12}
REG_IDX = {"r0": 0, "r1": 1, "r2": 2, "r3": 3, "r4": 4, "r5": 5, "r6": 6, "r7": 7,
           "r8": 8, "sb": 9, "sl": 10, "fp": 11, "r9": 9, "r10": 10, "r11": 11, "r12": 12, "ip": 12}


class Emu:
    def __init__(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.elf = ELFFile(open(SO, "rb"))
        self.hooks = {}
        self.next_hook = HOOK_ADDR
        self.heap_top = HEAP_ADDR + 0x1000
        self.jstr_next = JSTR_ADDR + 0x1000
        self.jstr_data = {}
        self.jstr_len = {}
        self.md5_inputs = []
        self.manual = {}  # 地址 -> 指令（手动模拟）

    def load(self):
        for seg in self.elf.iter_segments():
            if seg['p_type'] != 'PT_LOAD':
                continue
            vaddr = seg['p_vaddr']
            map_addr = vaddr & ~0xFFF
            off = vaddr - map_addr
            size = (off + seg['p_memsz'] + 0xFFF) & ~0xFFF
            self.uc.mem_map(map_addr, size)
            d = seg.data()
            if d:
                self.uc.mem_write(vaddr, d)
        self.uc.mem_map(STACK_ADDR, 0x100000)
        self.uc.mem_map(HEAP_ADDR, 0x4000000)
        self.uc.mem_map(HOOK_ADDR, 0x3000000)

    def relocate(self):
        dynsym = self.elf.get_section_by_name(".dynsym")
        sym_addr = {}
        for s in dynsym.iter_symbols():
            if s['st_value']:
                sym_addr[s.name] = s['st_value']
        for sec in self.elf.iter_sections():
            if not isinstance(sec, RelocationSection):
                continue
            for rel in sec.iter_relocations():
                t = rel['r_info_type']
                off = rel['r_offset']
                name = dynsym.get_symbol(rel['r_info_sym']).name if rel['r_info_sym'] else None
                if t == 23:
                    addend = struct.unpack("<I", self.uc.mem_read(off, 4))[0]
                    self.uc.mem_write(off, struct.pack("<I", addend))
                elif t in (21, 2, 22):
                    val = sym_addr.get(name, 0)
                    if name not in sym_addr:
                        val = self._alloc(name)
                    if t == 2:
                        addend = struct.unpack("<I", self.uc.mem_read(off, 4))[0]
                        val = (val + addend) & 0xFFFFFFFF
                    self.uc.mem_write(off, struct.pack("<I", val))

    def _alloc(self, name):
        if name in self.hooks:
            return self.hooks[name]
        a = self.next_hook | 1
        self.next_hook += 4
        self.hooks[name] = a
        return a

    def _hook(self, uc, addr, size, user):
        addr &= ~1
        # PLT 拦截（ARM 代码，Unicorn Thumb 模式无法执行）
        if 0x7a530 <= addr < 0x7c470:
            self._plt(addr)
            return
        for name, ha in self.hooks.items():
            if (ha & ~1) == addr:
                if name.startswith("JNI_"):
                    self._jni(name[4:])
                else:
                    self._ext(name)
                return
        if addr == MD5:
            self._md5()
            return
        if addr in self.manual:
            ins = self.manual[addr]
            self._manual(ins)
            return

    def _plt(self, addr):
        code = self.uc.mem_read(addr, 12)
        md_arm = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        insns = list(md_arm.disasm(code, addr))
        base = None
        off = None
        for ins in insns:
            if ins.mnemonic == "add" and ins.op_str.startswith("ip, pc"):
                base = ins.address + 8
            elif ins.mnemonic == "add" and ins.op_str.startswith("ip, ip"):
                imm = int(ins.op_str.split("#")[1], 16)
                base = (base + imm) & 0xFFFFFFFF
            elif ins.mnemonic == "ldr" and "pc" in ins.op_str:
                off = int(ins.op_str.split("#")[1].split("]")[0].rstrip("!"), 16)
        if base is not None and off is not None:
            got = (base + off) & 0xFFFFFFFF
            val = struct.unpack("<I", self.uc.mem_read(got, 4))[0]
            self.uc.reg_write(UC_ARM_REG_PC, val)
        else:
            self.uc.reg_write(UC_ARM_REG_PC, addr + 4)

    def _manual(self, ins):
        uc = self.uc
        if ins.mnemonic == "push.w":
            regs = [r.strip() for r in ins.op_str.strip("{}").split(",")]
            regs = [r for r in regs if r not in ("", " ")]
            sp = uc.reg_read(UC_ARM_REG_SP) - 4 * len(regs)
            uc.reg_write(UC_ARM_REG_SP, sp)
            for i, r in enumerate(regs):
                r = r.strip()
                if r in REG_IDX:
                    val = uc.reg_read(REG_IDX[r])
                    uc.mem_write(sp + i * 4, struct.pack("<I", val))
        elif ins.mnemonic == "sub" and ins.op_str.startswith("sp"):
            imm = int(ins.op_str.split("#")[1], 16) if "#" in ins.op_str else int(ins.op_str.split("#0x")[1].split("]")[0], 16)
            uc.reg_write(UC_ARM_REG_SP, uc.reg_read(UC_ARM_REG_SP) - imm)
        elif ins.mnemonic == "mov":
            dst, src = [x.strip() for x in ins.op_str.split(",")]
            if dst in REG_IDX and src in REG_IDX:
                uc.reg_write(REG_IDX[dst], uc.reg_read(REG_IDX[src]))
        uc.reg_write(UC_ARM_REG_PC, ins.address + ins.size)

    def _ext(self, name):
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
        elif name == "free":
            ret = 0
        elif name in ("memcpy", "__aeabi_memcpy", "memmove", "__aeabi_memmove"):
            try:
                if 0 < r2 < 0x100000:
                    uc.mem_write(r0, uc.mem_read(r1, r2))
            except Exception:
                pass
            ret = r0
        elif name in ("memset", "__aeabi_memset", "__aeabi_memclr"):
            try:
                if r2 < 0x100000:
                    uc.mem_write(r0, b"\x00" * r2 if name == "__aeabi_memclr" else bytes([r1 & 0xFF]) * r2)
            except Exception:
                pass
            ret = r0
        elif name == "memcmp":
            a = uc.mem_read(r0, r2); b = uc.mem_read(r1, r2)
            ret = 0 if a == b else (1 if a > b else -1)
        elif name in ("strlen", "__strlen_chk"):
            p = r0; n = 0
            while uc.mem_read(p, 1) != b"\x00" and n < 4096:
                n += 1; p += 1
            ret = n
        elif name == "strcmp":
            a = self._cstr(r0); b = self._cstr(r1)
            ret = 0 if a == b else (1 if a > b else -1)
        elif name == "time":
            ret = 1788059615
        else:
            ret = 0
        uc.reg_write(UC_ARM_REG_R0, ret)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def _cstr(self, a):
        if a == 0:
            return b""
        p = a; d = b""
        while uc.mem_read(p, 1) != b"\x00" and len(d) < 4096:
            d += uc.mem_read(p, 1); p += 1
        return d

    def _jni(self, name):
        uc = self.uc
        r1 = uc.reg_read(UC_ARM_REG_R1)
        lr = uc.reg_read(UC_ARM_REG_LR)
        ret = 0
        if name in ("GetStringUTFLength", "GetStringLength"):
            ret = self.jstr_len.get(r1, 0)
        elif name == "GetStringUTFChars":
            ret = self.jstr_data.get(r1, 0)
        elif name == "ReleaseStringUTFChars":
            ret = 0
        elif name == "FindClass":
            ret = 0x5000
        elif name in ("GetStaticMethodID", "GetMethodID"):
            ret = 0x6000
        elif name == "CallStaticObjectMethodA":
            ret = self._make_jstring(b"TEST_DEVICE_ID_FAKE")
        elif name == "IsInstanceOf":
            ret = 1
        else:
            ret = 0
        uc.reg_write(UC_ARM_REG_R0, ret)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def _make_jstring(self, data):
        p = self.jstr_next
        self.uc.mem_write(p, data + b"\x00")
        self.jstr_next += len(data) + 16
        j = self.jstr_next
        self.jstr_data[j] = p
        self.jstr_len[j] = len(data)
        self.jstr_next += 16
        return j

    def _md5(self):
        uc = self.uc
        r1 = uc.reg_read(UC_ARM_REG_R1)
        b0 = uc.mem_read(r1, 1)[0]
        if b0 & 1:
            ln = struct.unpack("<I", uc.mem_read(r1 + 4, 4))[0]
            ptr = struct.unpack("<I", uc.mem_read(r1 + 8, 4))[0]
        else:
            ln = b0 >> 1
            ptr = r1 + 1
        data = uc.mem_read(ptr, ln) if ln else b""
        self.md5_inputs.append(data)
        print(f"[MD5] 输入 {ln} 字节: {data!r}")

    def run(self, path, key, ts):
        self.load()
        self.relocate()
        for off, name in JNI_OFFSETS.items():
            ha = self._alloc("JNI_" + name)
            self.uc.mem_write(JNIENV_ADDR + off, struct.pack("<I", ha))
        self.uc.hook_add(UC_HOOK_CODE, self._hook, begin=HOOK_ADDR, end=HOOK_ADDR + 0x1000000)
        self.uc.hook_add(UC_HOOK_CODE, self._hook, begin=MD5 & ~1, end=(MD5 & ~1) | 1)
        pj = self._make_jstring(path.encode())
        kj = self._make_jstring(key.encode())
        sp = STACK_ADDR + 0x100000 - 0x100
        self.uc.mem_write(sp, struct.pack("<I", ts))
        self.uc.reg_write(UC_ARM_REG_SP, sp)
        self.uc.reg_write(UC_ARM_REG_R0, JNIENV_ADDR)
        self.uc.reg_write(UC_ARM_REG_R1, 0x1111)
        self.uc.reg_write(UC_ARM_REG_R2, pj)
        self.uc.reg_write(UC_ARM_REG_R3, kj)
        self.uc.reg_write(UC_ARM_REG_LR, 0xDEADBEEF)
        # 自动 hook 循环
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        for _ in range(200):
            try:
                self.uc.emu_start(FN | 1, 0xDEADBEEF, timeout=5 * UC_SECOND_SCALE, count=100000)
                break
            except UcError as e:
                pc = self.uc.reg_read(UC_ARM_REG_PC)
                addr = pc & ~1
                if addr in self.manual:
                    break
                code = self.uc.mem_read(addr, 4)
                ins = next(md.disasm(code, addr))
                print(f"[hook] 0x{addr:x}: {ins.mnemonic} {ins.op_str}")
                self.manual[addr] = ins
                self.uc.hook_add(UC_HOOK_CODE, self._hook, begin=addr, end=addr | 1)
        print("MD5 输入条数:", len(self.md5_inputs))


if __name__ == "__main__":
    e = Emu()
    e.run("/leo-game-pk/android/math/pk/match/v2", "wdi4n2t8edr", 1788059161)
