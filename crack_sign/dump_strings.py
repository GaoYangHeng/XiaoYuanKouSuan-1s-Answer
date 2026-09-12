from elftools.elf.elffile import ELFFile
import re

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

with open(SO, "rb") as f:
    elf = ELFFile(f)
    # 遍历 .rodata 和 .data.rel.ro，提取可打印字符串
    for secname in [".rodata", ".data.rel.ro", ".data"]:
        sec = elf.get_section_by_name(secname)
        if not sec:
            continue
        data = sec.data()
        base = sec['sh_addr']
        print(f"\n===== {secname} (0x{base:x}) 字符串 =====")
        # 找连续可打印 ASCII 序列
        for m in re.finditer(rb"[\x20-\x7e]{4,}", data):
            s = m.group().decode()
            print(f"0x{base + m.start():08x}: {s!r}")
