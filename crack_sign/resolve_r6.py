from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"


def read_va(elf, va, size):
    for seg in elf.iter_segments():
        if seg["p_type"] != "PT_LOAD":
            continue
        if seg["p_vaddr"] <= va < seg["p_vaddr"] + seg["p_memsz"]:
            return seg.data()[va - seg["p_vaddr"]: va - seg["p_vaddr"] + size]
    return None


with open(SO, "rb") as f:
    elf = ELFFile(f)

    # 找 0x80a36 的 RELATIVE 重定位（值为内部函数地址）
    for sec in elf.iter_sections():
        if not isinstance(sec, RelocationSection):
            continue
        for rel in sec.iter_relocations():
            if rel["r_offset"] == 0x80a36:
                print(f"0x80a36: type={rel['r_info_type']} sym={rel['r_info_sym']}")
                if rel["r_info_type"] == 23:  # RELATIVE
                    # addend 在 GOT 项里（未重定位时为 0，addend 在重定位表）
                    addend = rel["r_info_sym"]  # 对 RELATIVE，sym 字段存 addend 高位
                    print(f"  RELATIVE addend 高16位={addend}")
    # 直接读 GOT 项（静态文件里 RELATIVE 的 addend 通常存在重定位的 r_addend）
    for sec in elf.iter_sections():
        if isinstance(sec, RelocationSection):
            for rel in sec.iter_relocations():
                if rel["r_offset"] == 0x80a36:
                    ea = rel.entry
                    if "r_addend" in ea:
                        print(f"  r_addend = 0x{ea['r_addend']:x}")
                    else:
                        v = struct.unpack("<I", read_va(elf, 0x80a36, 4))[0]
                        print(f"  GOT 静态值 = 0x{v:x} (RELATIVE 目标)")
