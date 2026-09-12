from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"


def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec["sh_addr"]
        s = sec["sh_size"]
        if a <= va < a + s:
            return sec.data()[va - a: va - a + size]
    return None


with open(SO, "rb") as f:
    elf = ELFFile(f)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    code = read_va(elf, 0x41bdd, 0x100)
    for ins in md.disasm(code, 0x41bdd):
        print(f"0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")
