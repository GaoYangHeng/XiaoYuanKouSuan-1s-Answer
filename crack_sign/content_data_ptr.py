from elftools.elf.elffile import ELFFile

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libContentEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec['sh_addr']
        s = sec['sh_size']
        if a <= va < a + s:
            off = va - a
            return sec.data()[off:off+size]
    return None

with open(SO, "rb") as f:
    elf = ELFFile(f)

    # .data 里的指针指向的字符串
    for addr in [0x18571, 0x1864d, 0x10e61, 0x10e06]:
        data = read_va(elf, addr, 64)
        print(f"0x{addr:08x}: {data[:48]!r}")

    # 解析 0x12ca4 的 GOT 访问：读字面量池 0x1305c
    print("\n=== 字面量池 0x13040~0x13080 ===")
    data = read_va(elf, 0x13040, 0x40)
    import struct
    for i in range(0, len(data), 4):
        v = struct.unpack("<I", data[i:i+4])[0]
        print(f"0x{0x13040+i:08x}: 0x{v:08x}")
