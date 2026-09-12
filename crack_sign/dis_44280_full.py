from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM
import struct, re

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

    def plt_sym(entry):
        mda = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        code = read_va(elf, entry, 12)
        insns = list(mda.disasm(code, entry))
        if len(insns) < 3:
            return None
        m = re.search(r"#(0x[0-9a-f]+)", insns[2].op_str)
        if not m:
            return None
        imm = int(m.group(1), 16)
        got = entry + 0x6014 + imm
        return slots.get(got, f"GOT0x{got:x}")

    mdt = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    start, size = 0x44280, 0x1c0
    code = read_va(elf, start, size)
    for ins in mdt.disasm(code, start):
        line = f"0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}"
        if ins.mnemonic == "bl" and ins.op_str.startswith("#0x"):
            tgt = int(ins.op_str[1:], 16)
            if 0x79000 <= tgt <= 0x7c000:
                line += f"   ; PLT {plt_sym(tgt)}"
        if ins.mnemonic == "blx" and ins.op_str.startswith("#0x"):
            tgt = int(ins.op_str[1:], 16)
            if 0x79000 <= tgt <= 0x7c000:
                line += f"   ; PLT {plt_sym(tgt)}"
        print(line)
