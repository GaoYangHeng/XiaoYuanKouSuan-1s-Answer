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
    data = read_va(elf, 0x414e6, 0x40)
    print(data.hex())
