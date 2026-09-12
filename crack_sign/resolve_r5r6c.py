from elftools.elf.elffile import ELFFile
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"


def read_va(elf, va, size):
    for seg in elf.iter_segments():
        if seg["p_type"] != "PT_LOAD":
            continue
        p_vaddr = seg["p_vaddr"]
        p_memsz = seg["p_memsz"]
        if p_vaddr <= va < p_vaddr + p_memsz:
            return seg.data()[va - p_vaddr: va - p_vaddr + size]
    return None


with open(SO, "rb") as f:
    elf = ELFFile(f)
    dynsym = elf.get_section_by_name(".dynsym")

    for name, va in [("r5", 0x80a68), ("r6", 0x80a36)]:
        data = read_va(elf, va, 4)
        if data is None:
            print(f"{name}: VA 0x{va:x} 不可读")
            continue
        val = struct.unpack("<I", data)[0]
        print(f"{name}: GOT@0x{va:x} = 0x{val:x}")
        # 符号解析（st_value 匹配）
        hit = None
        for sym in dynsym.iter_symbols():
            if sym["st_value"] == (val & ~1) or sym["st_value"] == val:
                hit = sym.name
                break
        print(f"  符号: {hit if hit else '<未找到，可能是导入函数>'}")

        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        tgt = val & ~1
        code = read_va(elf, tgt, 0x40)
        if code:
            print(f"  反汇编 0x{tgt:x}:")
            for ins in md.disasm(code, tgt):
                print(f"    0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")
                if ins.address >= tgt + 0x30:
                    break
        print()
