from elftools.elf.elffile import ELFFile

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
    data = read_va(elf, 0x414c0, 0x30)
    print("bytes:", data.hex())
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for ins in md.disasm(data, 0x414c0):
        print(f"0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")
