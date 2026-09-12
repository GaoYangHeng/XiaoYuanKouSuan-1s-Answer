import struct
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libContentEncoder.so"

with open(SO, "rb") as f:
    elf = ELFFile(f)

    # 读 .got 段原始数据
    got = elf.get_section_by_name(".got")
    gotd = got.data()
    got_base = got['sh_addr']
    print(f".got base=0x{got_base:08x} size={len(gotd)}")

    # 读 0x28f7c 的原始值
    off = 0x28f7c - got_base
    v = struct.unpack("<I", gotd[off:off+4])[0]
    print(f"GOT[0x28f7c] = 0x{v:08x}")

    # 找 .rel.dyn 里 off 在 0x28f7c 附近的重定位
    print("\n=== .rel.dyn 重定位（off 0x28f70~0x28f90）===")
    rel = elf.get_section_by_name(".rel.dyn")
    for r in rel.iter_relocations():
        if 0x28f70 <= r['r_offset'] <= 0x28f90:
            sym = r['r_info_sym']
            typ = r['r_info_type']
            # 符号名
            symtab = elf.get_section_by_name('.dynsym')
            sname = symtab.get_symbol(sym).name if sym else ''
            addend = None
            if r.is_RELA():
                addend = r['r_addend']
            print(f"off=0x{r['r_offset']:08x} type={typ} sym={sname} addend={addend}")

    # .bss 段
    bss = elf.get_section_by_name(".bss")
    print(f"\n.bss base=0x{bss['sh_addr']:08x} size=0x{bss['sh_size']:08x}")
