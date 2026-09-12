import struct
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from unicorn import *
from unicorn.arm_const import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

HEAP_ADDR = 0x80000000
HOOK_ADDR = 0x90000000
STACK_ADDR = 0x6f000000


class Sim:
    def __init__(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.elf = ELFFile(open(SO, "rb"))
        self.hook_entries = {}
        self.next_hook = HOOK_ADDR
        self.heap_top = HEAP_ADDR + 0x1000

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
        self.uc.mem_map(STACK_ADDR, 0x100000)
        self.uc.mem_map(HEAP_ADDR, 0x4000000)
        self.uc.mem_map(HOOK_ADDR, 0x1000000)

    def resolve(self):
        dynsym = self.elf.get_section_by_name(".dynsym")
        self.sym_addr = {}
        for sym in dynsym.iter_symbols():
            if sym['st_value']:
                self.sym_addr[sym.name] = sym['st_value']

    def relocate(self):
        self.resolve()
        dynsym = self.elf.get_section_by_name(".dynsym")
        for sec in self.elf.iter_sections():
            if not isinstance(sec, RelocationSection):
                continue
            for rel in sec.iter_relocations():
                t = rel['r_info_type']
                off = rel['r_offset']
                sym = rel['r_info_sym']
                name = dynsym.get_symbol(sym).name if sym else None
                if t == 23:  # R_ARM_RELATIVE
                    addend = struct.unpack("<I", self.uc.mem_read(off, 4))[0]
                    self.uc.mem_write(off, struct.pack("<I", addend))
                elif t in (21, 2, 22):  # GLOB_DAT/ABS32/JUMP_SLOT
                    val = self.sym_addr.get(name, 0)
                    if name is None or name not in self.sym_addr:
                        val = self._hook(name)
                    if t == 2:
                        addend = struct.unpack("<I", self.uc.mem_read(off, 4))[0]
                        val = (val + addend) & 0xFFFFFFFF
                    self.uc.mem_write(off, struct.pack("<I", val))

    def _hook(self, name):
        if name in self.hook_entries:
            return self.hook_entries[name]
        a = self.next_hook | 1
        self.next_hook += 4
        self.hook_entries[name] = a
        return a

    def _hook_code(self, uc, addr, size, user):
        addr &= ~1
        for name, ha in self.hook_entries.items():
            if (ha & ~1) == addr:
                self._handle(name)
                return

    def _handle(self, name):
        uc = self.uc
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        lr = uc.reg_read(UC_ARM_REG_LR)
        ret = 0
        if name == "malloc":
            ret = self.heap_top
            self.heap_top = (self.heap_top + r0 + 0xF) & ~0xF
        elif name == "free":
            ret = 0
        elif name in ("memcpy", "__aeabi_memcpy", "memmove", "__aeabi_memmove"):
            try:
                if r2 > 0 and r2 < 0x100000:
                    self.uc.mem_write(r0, self.uc.mem_read(r1, r2))
            except Exception:
                pass
            ret = r0
        elif name in ("memset", "__aeabi_memset"):
            try:
                if r2 < 0x100000:
                    self.uc.mem_write(r0, bytes([r1 & 0xFF]) * r2)
            except Exception:
                pass
            ret = r0
        elif name in ("strlen", "__strlen_chk"):
            p = r0
            n = 0
            while self.uc.mem_read(p, 1) != b"\x00" and n < 4096:
                n += 1
                p += 1
            ret = n
        else:
            ret = 0
        uc.reg_write(UC_ARM_REG_R0, ret)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def run(self, fn_addr, out_addr):
        self.load()
        self.relocate()
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code, begin=HOOK_ADDR, end=HOOK_ADDR + 0x1000000)
        sp = STACK_ADDR + 0x100000 - 0x100
        self.uc.reg_write(UC_ARM_REG_SP, sp)
        self.uc.reg_write(UC_ARM_REG_R0, out_addr)
        self.uc.reg_write(UC_ARM_REG_LR, 0xDEADBEEF)
        try:
            self.uc.emu_start(fn_addr | 1, 0xDEADBEEF, timeout=5 * UC_SECOND_SCALE, count=50000)
        except UcError as e:
            pc = self.uc.reg_read(UC_ARM_REG_PC)
            print(f"UcError {e} at 0x{pc:x}")
        # 读取 std::string
        b0 = self.uc.mem_read(out_addr, 1)[0]
        if b0 & 1:
            ln = struct.unpack("<I", self.uc.mem_read(out_addr + 4, 4))[0]
            ptr = struct.unpack("<I", self.uc.mem_read(out_addr + 8, 4))[0]
        else:
            ln = b0 >> 1
            ptr = out_addr + 1
        data = self.uc.mem_read(ptr, ln) if ln else b""
        return data


if __name__ == "__main__":
    for fn in [0x4a6ac, 0x451f8, 0x45f00]:
        s = Sim()
        out = HEAP_ADDR + 0x80000
        data = s.run(fn, out)
        print(f"0x{fn:x} 输出:", repr(bytes(data)))


