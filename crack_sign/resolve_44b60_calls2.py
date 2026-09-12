from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec["sh_addr"]; s = sec["sh_size"]
        if a <= va < a + s:
            return sec.data()[va - a: va - a + size], sec.name
    return None, None

with open(SO, "rb") as f:
    elf = ELFFile(f)
    dynsym = elf.get_section_by_name(".dynsym")
    relplt = elf.get_section_by_name(".rel.plt")
    slots = {}
    for rel in relplt.iter_relocations():
        sym = dynsym.get_symbol(rel['r_info_sym'])
        slots[rel['r_offset']] = sym.name

    def resolve_plt(entry):
        mda = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        code, _ = read_va(elf, entry, 12)
        insns = list(mda.disasm(code, entry))
        if len(insns) < 3:
            return None
        ldr_ins = insns[2]
        imm = int(ldr_ins.op_str.split("#")[1].split("]")[0], 16)
        got = entry + 0x6014 + imm
        return got, slots.get(got, "???")

    for entry in (0x7a8a0, 0x795d0):
        r = resolve_plt(entry)
        print(f"PLT 0x{entry:08x} -> {r}")

    # 0x7a084 / 0x7a044 不是 16 对齐，反汇编看看
    mda = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    mdt = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for addr in (0x7a084, 0x7a044):
        code, sname = read_va(elf, addr, 16)
        print(f"\n=== 0x{addr:08x} (段 {sname}) ARM 解释 ===")
        for ins in mda.disasm(code, addr):
            print(f"  0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")
        print(f"--- THUMB 解释 ---")
        for ins in mdt.disasm(code, addr):
            print(f"  0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")

    # 反汇编 0x44a48
    print("\n=== 0x44a48 (THUMB) ===")
    code, _ = read_va(elf, 0x44a48, 0x40)
    for ins in mdt.disasm(code, 0x44a48):
        print(f"  0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")

    # 反汇编 0x43338 (sb) 和 0x43c04 (sl)
    for base in (0x43338, 0x43c04):
        print(f"\n=== 0x{base:08x} (THUMB) ===")
        code, _ = read_va(elf, base, 0x40)
        for ins in mdt.disasm(code, base):
            print(f"  0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")
