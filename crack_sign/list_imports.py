from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

with open(SO, "rb") as f:
    elf = ELFFile(f)
    # 动态符号表里未定义（导入）的符号
    dynsym = elf.get_section_by_name(".dynsym")
    print("=== 导入的外部函数 ===")
    for sym in dynsym.iter_symbols():
        if sym['st_shndx'] == 'SHN_UNDEF' and sym['st_info']['type'] == 'STT_FUNC':
            print(sym.name)
    print("\n=== 重定位类型统计 ===")
    from collections import Counter
    c = Counter()
    for secname in [".rel.dyn", ".rel.plt"]:
        sec = elf.get_section_by_name(secname)
        if sec:
            for rel in sec.iter_relocations():
                c[rel['r_info_type']] += 1
    for k, v in c.items():
        print(f"type {k}: {v}")
