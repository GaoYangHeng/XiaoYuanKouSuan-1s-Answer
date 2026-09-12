from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM
import re

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec["sh_addr"]; s = sec["sh_size"]
        if a <= va < a + s:
            return sec.data()[va - a: va - a + size], sec.name
    return None, None

with open(SO, "rb") as f:
    elf = ELFFile(f)
    dynsym = elf.get_section_by_name(".dynsym")
    relplt = elf.get_section_by_name(".rel.plt")
    slots = {}
    for rel in relplt.iter_relocations():
        slots[rel["r_offset"]] = dynsym.get_symbol(rel["r_info_sym"]).name

    def plt_sym(entry):
        mda = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        code, _ = read_va(elf, entry, 12)
        insns = list(mda.disasm(code, entry))
        if len(insns) < 3:
            return None
        m = re.search(r"#(0x[0-9a-f]+)", insns[2].op_str)
        if not m:
            return None
        got = entry + 0x6014 + int(m.group(1), 16)
        return slots.get(got, f"GOT0x{got:x}")

    print("0x7a760 ->", plt_sym(0x7a760))

    # 0x51248 在哪个段
    d, sname = read_va(elf, 0x51248, 4)
    print(f"0x51248 段: {sname}, 值: {d.hex() if d else None}")

    mdt = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    # 0x42247 上下文
    print("\n=== 0x421f0 ~ 0x42280 (LR=0x42247) ===")
    code, _ = read_va(elf, 0x421f0, 0x90)
    for ins in mdt.disasm(code, 0x421f0):
        mark = "  <-- LR" if ins.address == 0x42247 else ""
        print(f"  0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}{mark}")
