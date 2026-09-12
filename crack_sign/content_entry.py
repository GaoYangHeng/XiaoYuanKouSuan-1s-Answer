from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libContentEncoder.so"

with open(SO, "rb") as f:
    elf = ELFFile(f)

    print("=== .text 等代码段 ===")
    for sec in elf.iter_sections():
        if sec.name in (".text", ".plt", ".init", ".fini"):
            print(f"{sec.name:10s} addr=0x{sec['sh_addr']:08x} size=0x{sec['sh_size']:08x}")

    print("\n=== 动态导出符号（非 _Z / 非 C++ 运行时）===")
    dynsym = elf.get_section_by_name(".dynsym")
    for sym in dynsym.iter_symbols():
        if sym['st_shndx'] != 'SHN_UNDEF' and sym['st_value']:
            nm = sym.name
            if not nm.startswith('_Z'):
                print(f"{nm:50s} value=0x{sym['st_value']:08x} size=0x{sym['st_size']:x}")

    print("\n=== 所有含 Java/JNI/Register/OnLoad/c 的符号 ===")
    for sec in elf.iter_sections():
        if isinstance(sec, SymbolTableSection):
            for sym in sec.iter_symbols():
                if sym['st_value'] and sym['st_info']['type'] in ('STT_FUNC', 'STT_NOTYPE'):
                    nm = sym.name
                    if any(k in nm for k in ('Java_', 'JNI', 'Register', 'OnLoad')):
                        print(f"{nm:60s} value=0x{sym['st_value']:08x} size=0x{sym['st_size']:x}")

    print("\n=== 重定位（.rel.dyn/.rel.plt 里对 .text 的引用，找 JUMP_SLOT 目标）===")
    for secname in [".rel.dyn", ".rel.plt"]:
        sec = elf.get_section_by_name(secname)
        if not sec:
            continue
        for rel in sec.iter_relocations():
            symtab = dynsym
            sym = symtab.get_symbol(rel['r_info_sym'])
            off = rel['r_offset']
            if sym.name and not sym.name.startswith('_Z'):
                print(f"{secname} off=0x{off:08x} -> {sym.name}")
