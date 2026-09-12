from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB
import struct

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
    # .plt 是 ARM 模式（不是 Thumb）
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    md.detail = True
    code = read_va(elf, 0x25c20, 0x80)
    print("=== .plt 段（ARM 模式）===")
    for ins in md.disasm(code, 0x25c20):
        print(f"0x{ins.address:08x}: {ins.mnemonic:12s} {ins.op_str}")

    # 关联 GOT.plt：读 rel.plt 里的 JUMP_SLOT 重定位（按 r_offset 排序）
    print("\n=== .rel.plt JUMP_SLOT（按 offset 排序）===")
    relplt = elf.get_section_by_name(".rel.plt")
    dynsym = elf.get_section_by_name(".dynsym")
    items = []
    for rel in relplt.iter_relocations():
        sym = dynsym.get_symbol(rel['r_info_sym'])
        items.append((rel['r_offset'], sym.name))
    items.sort()
    for off, name in items:
        print(f"GOT.plt 0x{off:08x} -> {name}")
