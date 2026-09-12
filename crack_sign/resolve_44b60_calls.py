from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec["sh_addr"]; s = sec["sh_size"]
        if a <= va < a + s:
            return sec.data()[va - a: va - a + size]
    return None

with open(SO, "rb") as f:
    elf = ELFFile(f)
    dynsym = elf.get_section_by_name(".dynsym")
    relplt = elf.get_section_by_name(".rel.plt")
    slots = {}
    for rel in relplt.iter_relocations():
        sym = dynsym.get_symbol(rel['r_info_sym'])
        slots[rel['r_offset']] = sym.name

    # 反汇编 PLT 桩 0x7a590 / 0x7a5b0 (ARM 态)
    mda = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    print("=== PLT 桩反汇编 ===")
    for base in (0x7a590, 0x7a5b0):
        code = read_va(elf, base, 12)
        insns = list(mda.disasm(code, base))
        for ins in insns:
            print(f"  0x{ins.address:08x}: {ins.mnemonic:8s} {ins.op_str}")
        # entry = base (ldr 在 entry+8)
        ldr_ins = insns[2]
        imm = int(ldr_ins.op_str.split("#")[1].split("]")[0], 16)
        got_slot = base + 0x6014 + imm
        print(f"    -> GOT 0x{got_slot:08x} = {slots.get(got_slot, '???')}")

    # rel.dyn 里 .got 区段的符号
    print("\n=== .rel.dyn 中 .got 区段 (0x8081c~0x80834) 符号 ===")
    reldyn = elf.get_section_by_name(".rel.dyn")
    for rel in reldyn.iter_relocations():
        off = rel["r_offset"]
        if 0x8081c <= off < 0x80834:
            sym = dynsym.get_symbol(rel["r_info_sym"])
            print(f"  0x{off:08x} type={rel['r_info_type']} = {sym.name}")

    # 反汇编 0x41c48 (r4 指向的字符串函数)
    print("\n=== 0x41c48 (r4) ===")
    mdt = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    code = read_va(elf, 0x41c48, 0x60)
    for ins in mdt.disasm(code, 0x41c48):
        print(f"  0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")

    # 反汇编 0x44280 (构造 sp+0x28)
    print("\n=== 0x44280 ===")
    code = read_va(elf, 0x44280, 0x60)
    for ins in mdt.disasm(code, 0x44280):
        print(f"  0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")
