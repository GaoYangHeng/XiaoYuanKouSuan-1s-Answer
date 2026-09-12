from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec["sh_addr"]; s = sec["sh_size"]
        if a <= va < a + s:
            return sec.data()[va - a: va - a + size]
    return None

with open(SO, "rb") as f:
    elf = ELFFile(f)
    mdt = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for base, sz in ((0x453fc, 0x80), (0x455c0, 0x60), (0x45660, 0x60)):
        print(f"\n=== 0x{base:08x} ===")
        code = read_va(elf, base, sz)
        for ins in mdt.disasm(code, base):
            print(f"  0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")
