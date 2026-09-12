from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB
import struct

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

    # 0x4afb6: ldr r0,[pc,#0x24] -> lit @0x4afdc
    d, _ = read_va(elf, 0x4afdc, 4)
    lit = struct.unpack("<I", d)[0]
    pc = 0x4afbc  # add r0, pc 的 pc = 0x4afb8+4
    got = pc + lit
    print(f"0x4afb6 lit@0x4afdc = 0x{lit:x} -> GOT槽 0x{got:x}")
    d2, _ = read_va(elf, got, 4)
    print(f"  GOT值 = 0x{struct.unpack('<I', d2)[0]:x}")

    # rel.dyn 里该 GOT 槽符号
    reldyn = elf.get_section_by_name(".rel.dyn")
    for rel in reldyn.iter_relocations():
        if rel["r_offset"] == got:
            sym = dynsym.get_symbol(rel["r_info_sym"])
            print(f"  rel.dyn 符号 = {sym.name}")

    # 0x7abb0 符号
    def resolve_plt(entry):
        mda = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        code, _ = read_va(elf, entry, 12)
        insns = list(mda.disasm(code, entry))
        import re
        m = re.search(r"#(0x[0-9a-f]+)", insns[2].op_str)
        imm = int(m.group(1), 16)
        return entry + 0x6014 + imm, slots.get(entry + 0x6014 + imm, "???")
    print("0x7abb0 ->", resolve_plt(0x7abb0))

    # 0x51248 所在函数（str_ctor），反汇编看结构
    mdt = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("\n=== 0x51230 ~ 0x51280 (str_ctor 0x51248) ===")
    code, _ = read_va(elf, 0x51230, 0x60)
    for ins in mdt.disasm(code, 0x51230):
        mark = "  <-- hook" if ins.address == 0x51248 else ""
        print(f"  0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}{mark}")
