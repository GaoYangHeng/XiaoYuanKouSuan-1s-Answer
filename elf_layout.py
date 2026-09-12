from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

with open(SO, "rb") as f:
    elf = ELFFile(f)
    print("=== sections ===")
    for sec in elf.iter_sections():
        if sec['sh_size'] > 0:
            print("%-20s addr=0x%-8x off=0x%-8x size=0x%-7x" % (
                sec.name, sec['sh_addr'], sec['sh_offset'], sec['sh_size']))

    # 0x43388 属于哪个段
    off = 0x43388
    for sec in elf.iter_sections():
        if sec['sh_offset'] <= off < sec['sh_offset'] + sec['sh_size']:
            vaddr = sec['sh_addr'] + (off - sec['sh_offset'])
            print("\n0x43388 in section", sec.name, "-> vaddr 0x%x" % vaddr)

    # 动态符号表里找 JNI_OnLoad 和可能的函数
    print("\n=== dynamic symbols ===")
    for sec in elf.iter_sections():
        if isinstance(sec, SymbolTableSection):
            for sym in sec.iter_symbols():
                nm = sym.name
                if nm and ('JNI' in nm or 'Java' in nm or 'jni' in nm):
                    print("sym %s = 0x%x" % (nm, sym['st_value']))
