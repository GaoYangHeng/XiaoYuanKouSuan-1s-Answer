from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
import struct, re

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec["sh_addr"]; s = sec["sh_size"]
        if a <= va < a + s:
            return sec.data()[va - a: va - a + size], sec.name
    return None, None

with open(SO, "rb") as f:
    elf = ELFFile(f)
    mdt = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    start, size = 0x41a1e, 0x1a0
    code, _ = read_va(elf, start, size)
    for ins in mdt.disasm(code, start):
        print(f"0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")
