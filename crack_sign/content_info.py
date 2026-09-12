import re
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libContentEncoder.so"

with open(SO, "rb") as f:
    elf = ELFFile(f)

    print("=== 节区 ===")
    for sec in elf.iter_sections():
        print(f"{sec.name:20s} addr=0x{sec['sh_addr']:08x} off=0x{sec['sh_offset']:08x} size=0x{sec['sh_size']:08x}")

    print("\n=== 符号（FUNC/NOTYPE，含 JNI/Java/Register 相关）===")
    for sec in elf.iter_sections():
        if isinstance(sec, SymbolTableSection):
            for sym in sec.iter_symbols():
                if sym['st_value'] and sym['st_info']['type'] in ('STT_FUNC', 'STT_NOTYPE'):
                    nm = sym.name
                    if any(k in nm for k in ('JNI', 'Java_', 'Register', 'OnLoad', 'c')):
                        print(f"{nm:50s} value=0x{sym['st_value']:08x} size=0x{sym['st_size']:x}")

    print("\n=== 全部导出（.dynsym shndx!=UNDEF）===")
    dynsym = elf.get_section_by_name(".dynsym")
    for sym in dynsym.iter_symbols():
        if sym['st_shndx'] != 'SHN_UNDEF' and sym['st_value']:
            print(f"{sym.name:50s} value=0x{sym['st_value']:08x} size=0x{sym['st_size']:x}")

    print("\n=== 导入的外部函数 ===")
    for sym in dynsym.iter_symbols():
        if sym['st_shndx'] == 'SHN_UNDEF' and sym['st_info']['type'] == 'STT_FUNC':
            print(sym.name)

    print("\n=== .rodata/.data.rel.ro 字符串 ===")
    for secname in [".rodata", ".data.rel.ro", ".data"]:
        sec = elf.get_section_by_name(secname)
        if not sec:
            continue
        data = sec.data()
        base = sec['sh_addr']
        print(f"\n----- {secname} (0x{base:x}) -----")
        for m in re.finditer(rb"[\x20-\x7e]{4,}", data):
            s = m.group().decode()
            print(f"0x{base + m.start():08x}: {s!r}")
