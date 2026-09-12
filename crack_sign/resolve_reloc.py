from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from elftools.elf.sections import SymbolTableSection

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

targets = {0x80a68: "r5", 0x80a36: "r6"}

with open(SO, "rb") as f:
    elf = ELFFile(f)
    dynsym = elf.get_section_by_name(".dynsym")

    for sec in elf.iter_sections():
        if not isinstance(sec, RelocationSection):
            continue
        for rel in sec.iter_relocations():
            off = rel["r_offset"]
            if off in targets:
                sym = dynsym.get_symbol(rel["r_info_sym"])
                t = rel["r_info_type"]
                tname = {2: "ABS32", 21: "GLOB_DAT", 22: "JUMP_SLOT", 23: "RELATIVE"}.get(t, str(t))
                print(f"{targets[off]}: r_offset=0x{off:x} type={tname} sym={sym.name}")
