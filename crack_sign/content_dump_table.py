import struct
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

    # 查找表 0x13064（累积频率表，lower_bound 用，32bit 数组）
    print("=== 0x13064 起的 32-bit 表（前 80 项）===")
    data = read_va(elf, 0x13064, 0x200)
    for i in range(0, 80):
        v = struct.unpack("<I", data[i*4:i*4+4])[0]
        print(f"[{i:3d}] 0x{v:08x} = {v}")

    # 也看看 0x13064 之前的内容（可能表在更早）
    print("\n=== 0x12fe0 起 32-bit 表 ===")
    data2 = read_va(elf, 0x12fe0, 0x100)
    for i in range(0, 32):
        v = struct.unpack("<I", data2[i*4:i*4+4])[0]
        print(f"[{i:3d}] 0x{v:08x} = {v}")
