import sys
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

with open(SO, "rb") as f:
    elf = ELFFile(f)

    print("=== 节区 ===")
    for sec in elf.iter_sections():
        print(f"{sec.name:20s} addr=0x{sec['sh_addr']:08x} off=0x{sec['sh_offset']:08x} size=0x{sec['sh_size']:08x}")

    print("\n=== 符号 ===")
    for sec in elf.iter_sections():
        if isinstance(sec, SymbolTableSection):
            for sym in sec.iter_symbols():
                if sym['st_value'] and sym['st_info']['type'] in ('STT_FUNC', 'STT_NOTYPE'):
                    nm = sym.name
                    if any(k in nm for k in ('JNI', 'Java_', 'zcvsd', 'sdwiox', 'Register', 'OnLoad')):
                        print(f"{nm:40s} value=0x{sym['st_value']:08x} size=0x{sym['st_size']:x}")
