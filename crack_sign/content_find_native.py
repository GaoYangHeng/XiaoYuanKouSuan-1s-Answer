import struct
from elftools.elf.elffile import ELFFile

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libContentEncoder.so"

with open(SO, "rb") as f:
    elf = ELFFile(f)

    # 定位关键字符串地址
    def find_str(b, needle):
        return b.find(needle)

    ro = elf.get_section_by_name(".rodata")
    rod = ro.data()
    ro_base = ro['sh_addr']

    sig = b"([B)[B"
    sig_off = rod.find(sig)
    sig_addr = ro_base + sig_off
    print(f"'([B)[B' @ 0x{sig_addr:08x} (rodata+0x{sig_off:x})")

    # 找 "c" 字符串（c 后跟 \0，且前面是 \0 或非字母，避免匹配到单词中间）
    name_addr = None
    for i in range(len(rod) - 2):
        if rod[i:i+2] == b"c\x00" and (i == 0 or not (0x20 <= rod[i-1] <= 0x7e)):
            name_addr = ro_base + i
            print(f"'c' 候选 @ 0x{name_addr:08x} (rodata+0x{i:x})")
            break

    # 在 .rodata 和 .data.rel.ro 里搜索指向 sig_addr 的指针（JNINativeMethod 数组第2字段）
    for secname in [".rodata", ".data.rel.ro"]:
        sec = elf.get_section_by_name(secname)
        if not sec:
            continue
        d = sec.data()
        base = sec['sh_addr']
        pat = struct.pack("<I", sig_addr)
        idx = 0
        while True:
            idx = d.find(pat, idx)
            if idx < 0:
                break
            va = base + idx
            print(f"\n[{secname}] 发现指向 '([B)[B' 的指针 @ 0x{va:08x}")
            # JNINativeMethod = {name, sig, fnPtr}，sig 是第2字段，name 在 va-4，fnPtr 在 va+4
            if idx >= 4 and idx + 8 <= len(d):
                name_p = struct.unpack("<I", d[idx-4:idx])[0]
                fn_p = struct.unpack("<I", d[idx+4:idx+8])[0]
                print(f"  name_ptr = 0x{name_p:08x}")
                print(f"  fn_ptr   = 0x{fn_p:08x}")
            idx += 4
