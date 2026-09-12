from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
import sys

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libContentEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec['sh_addr']
        s = sec['sh_size']
        if a <= va < a + s:
            off = va - a
            return sec.data()[off:off+size]
    return None

start = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x12ad0
size = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x60

with open(SO, "rb") as f:
    elf = ELFFile(f)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    code = read_va(elf, start, size)
    for ins in md.disasm(code, start):
        print(f"0x{ins.address:08x}: {ins.mnemonic:12s} {ins.op_str}")
