from elftools.elf.elffile import ELFFile
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

# MD5 / SHA 特征常量
CONSTS = {
    "MD5_A0": 0x67452301,
    "MD5_B0": 0xefcdab89,
    "MD5_C0": 0x98badcfe,
    "MD5_D0": 0x10325476,
    "MD5_K0": 0xd76aa478,
    "MD5_K1": 0xe8c7b756,
    "SHA1_H0": 0x67452301,
    "SHA1_H1": 0xefcdab89,
    "SHA1_H4": 0xc3d2e1f0,
}

with open(SO, "rb") as f:
    elf = ELFFile(f)
    full = f.read()

    for name, val in CONSTS.items():
        pat = struct.pack("<I", val)
        idxs = []
        pos = 0
        while True:
            i = full.find(pat, pos)
            if i == -1:
                break
            idxs.append(i)
            pos = i + 1
        # 换算成虚拟地址
        vas = []
        for off in idxs:
            for sec in elf.iter_sections():
                a = sec['sh_addr']; s = sec['sh_size']
                o = sec['sh_offset']
                if o <= off < o + s:
                    vas.append(a + (off - o))
                    break
        print(f"{name} (0x{val:08x}): 出现 {len(idxs)} 次 -> {[hex(v) for v in vas]}")
