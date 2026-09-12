from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
import re

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec["sh_addr"]; s = sec["sh_size"]
        if a <= va < a + s:
            return sec.data()[va - a: va - a + size]
    return None

with open(SO, "rb") as f:
    elf = ELFFile(f)
    dynsym = elf.get_section_by_name(".dynsym")
    relplt = elf.get_section_by_name(".rel.plt")
    slots = {}
    for rel in relplt.iter_relocations():
        slots[rel["r_offset"]] = dynsym.get_symbol(rel["r_info_sym"]).name

    mda = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    def plt_sym(entry):
        code = read_va(elf, entry, 12)
        insns = list(mda.disasm(code, entry))
        if len(insns) < 3:
            return None
        m = re.search(r"#(0x[0-9a-f]+)", insns[2].op_str)
        if not m:
            return None
        got = entry + 0x6014 + int(m.group(1), 16)
        return slots.get(got, f"GOT0x{got:x}")

    for e in (0x7a5c0, 0x7a5f0, 0x7a084, 0x7a590, 0x7a8a0, 0x7a680):
        print(f"0x{e:08x} -> {plt_sym(e)}")
