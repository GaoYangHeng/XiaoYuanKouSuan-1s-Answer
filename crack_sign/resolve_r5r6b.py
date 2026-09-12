from elftools.elf.elffile import ELFFile
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"


def read_va(elf, va, size):
    # 用 PT_LOAD 段映射虚拟地址到文件偏移
    for seg in elf.iter_segments():
        if seg["p_type"] != "PT_LOAD":
            continue
        p_vaddr = seg["p_vaddr"]
        p_memsz = seg["p_memsz"]
        p_offset = seg["p_offset"]
        if p_vaddr <= va < p_vaddr + p_memsz:
            return seg.data()[va - p_vaddr: va - p_vaddr + size]
    return None


with open(SO, "rb") as f:
    elf = ELFFile(f)

    # 打印 PT_LOAD 段
    print("=== PT_LOAD 段 ===")
    for seg in elf.iter_segments():
        if seg["p_type"] == "PT_LOAD":
            print(f"vaddr=0x{seg['p_vaddr']:x} memsz=0x{seg['p_memsz']:x} off=0x{seg['p_offset']:x}")

    # r5/r6 的 GOT 项地址（从 PC-relative 计算）
    for name, va in [("r5", 0x7c868), ("r6", 0x7c836)]:
        data = read_va(elf, va, 4)
        if data is None:
            print(f"\n{name}: VA 0x{va:x} 不可读")
            continue
        val = struct.unpack("<I", data)[0]
        print(f"\n{name}: GOT@0x{va:x} = 0x{val:x}")
        # 解析该地址对应的符号
        dynsym = elf.get_section_by_name(".dynsym")
        for sym in dynsym.iter_symbols():
            if sym["st_value"] == (val & ~1):
                print(f"  符号: {sym.name}")
                break
        # 反汇编目标
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        tgt = val & ~1
        code = read_va(elf, tgt, 0x30)
        if code:
            print(f"  反汇编 0x{tgt:x}:")
            for ins in md.disasm(code, tgt):
                print(f"    0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")
                if ins.address >= tgt + 0x28:
                    break
