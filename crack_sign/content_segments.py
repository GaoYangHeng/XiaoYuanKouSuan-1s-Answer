from elftools.elf.elffile import ELFFile
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libContentEncoder.so"

with open(SO, "rb") as f:
    elf = ELFFile(f)

    print("=== 全部段 ===")
    for sec in elf.iter_sections():
        print(f"{sec.name:20s} addr=0x{sec['sh_addr']:08x} off=0x{sec['sh_offset']:08x} size=0x{sec['sh_size']:08x}")

    print("\n=== .init_array / .fini_array 内容 ===")
    for name in [".init_array", ".fini_array", ".preinit_array"]:
        sec = elf.get_section_by_name(name)
        if sec:
            d = sec.data()
            base = sec['sh_addr']
            for i in range(0, len(d), 4):
                v = struct.unpack("<I", d[i:i+4])[0]
                print(f"{name} [{i//4}] = 0x{v:08x}")

    print("\n=== .data 段 hex（前 128 字节）===")
    sec = elf.get_section_by_name(".data")
    if sec:
        d = sec.data()
        print("addr base=0x%08x size=%d" % (sec['sh_addr'], len(d)))
        for i in range(0, min(128, len(d)), 16):
            chunk = d[i:i+16]
            hexs = ' '.join(f"{b:02x}" for b in chunk)
            asc = ''.join(chr(b) if 0x20 <= b < 0x7f else '.' for b in chunk)
            print(f"0x{sec['sh_addr']+i:08x}: {hexs}  {asc}")

    print("\n=== .bss 段 ===")
    sec = elf.get_section_by_name(".bss")
    if sec:
        print(f".bss addr=0x{sec['sh_addr']:08x} size=0x{sec['sh_size']:08x}")

    print("\n=== .data.rel.ro 段 hex（前 128 字节）===")
    sec = elf.get_section_by_name(".data.rel.ro")
    if sec:
        d = sec.data()
        print("addr base=0x%08x size=%d" % (sec['sh_addr'], len(d)))
        for i in range(0, min(128, len(d)), 16):
            chunk = d[i:i+16]
            hexs = ' '.join(f"{b:02x}" for b in chunk)
            asc = ''.join(chr(b) if 0x20 <= b < 0x7f else '.' for b in chunk)
            print(f"0x{sec['sh_addr']+i:08x}: {hexs}  {asc}")
