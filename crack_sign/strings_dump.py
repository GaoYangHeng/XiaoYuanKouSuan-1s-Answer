from elftools.elf.elffile import ELFFile

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

with open(SO, "rb") as f:
    elf = ELFFile(f)
    for sec in elf.iter_sections():
        if sec.name not in (".rodata", ".data.rel.ro", ".data"):
            continue
        data = sec.data()
        print(f"\n===== {sec.name} (addr=0x{sec['sh_addr']:x}) =====")
        i = 0
        while i < len(data):
            if 0x20 <= data[i] < 0x7f:
                j = i
                while j < len(data) and 0x20 <= data[j] < 0x7f:
                    j += 1
                if j - i >= 4:
                    off = i
                    va = sec['sh_addr'] + i
                    print(f"0x{va:08x}: {data[i:j].decode('ascii', 'replace')}")
                    i = j
                else:
                    i += 1
            else:
                i += 1
