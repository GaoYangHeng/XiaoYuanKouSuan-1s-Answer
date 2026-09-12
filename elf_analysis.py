from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

sig_off = data.find(b"(Ljava/lang/String;Ljava/lang/String;I)Ljava/lang/String;")
print("sig_off:", hex(sig_off))

with open(SO, "rb") as f:
    elf = ELFFile(f)
    # 找 .rodata / .data.rel.ro 的地址映射
    for sec in elf.iter_sections():
        name = sec.name
        if "rodata" in name or "data.rel" in name:
            print("section", name, "addr=0x%x off=0x%x size=0x%x" % (sec['sh_addr'], sec['sh_offset'], sec['sh_size']))

    # 找重定位，定位 sig 字符串地址
    print("\n=== relocations referencing sig string region ===")
    for sec in elf.iter_sections():
        if not isinstance(sec, RelocationSection):
            continue
        for rel in sec.iter_relocations():
            r_off = rel['r_offset']
            # 读重定位处的值（通常是 addend 或 0）
            if r_off + 4 <= len(data):
                v = struct.unpack_from("<I", data, r_off)[0]
            else:
                v = None
            # 打印引用 sig 附近的重定位
            if rel['r_info_sym'] != 0:
                sym = elf.get_section(rel['r_info_sym'] if False else 0)
            print("reloc @0x%x type=%s sym=%d" % (r_off, rel['r_info_type'], rel['r_info_sym']))
