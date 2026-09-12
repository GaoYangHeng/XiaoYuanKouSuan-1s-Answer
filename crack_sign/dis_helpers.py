from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"


def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec["sh_addr"]
        s = sec["sh_size"]
        if a <= va < a + s:
            off = va - a
            return sec.data()[off:off + size]
    return None


with open(SO, "rb") as f:
    elf = ELFFile(f)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    for name, va, size in [
        ("0x41e74", 0x41e74, 0x54),
        ("0x41ec8", 0x41ec8, 0x50),
        ("0x41f7c", 0x41f7c, 0x80),
    ]:
        print(f"\n===== {name} =====")
        code = read_va(elf, va, size)
        for ins in md.disasm(code, va):
            print(f"0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")
