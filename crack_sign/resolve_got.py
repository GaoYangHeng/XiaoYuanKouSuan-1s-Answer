from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from elftools.elf.sections import SymbolTableSection
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"


def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec["sh_addr"]
        s = sec["sh_size"]
        if a <= va < a + s:
            return sec.data()[va - a: va - a + size]
    return None


with open(SO, "rb") as f:
    elf = ELFFile(f)

    # 建立 GOT 偏移 -> 符号名 映射
    dynsym = elf.get_section_by_name(".dynsym")
    got_relocs = {}
    for sec in elf.iter_sections():
        if isinstance(sec, RelocationSection):
            for rel in sec.iter_relocations():
                if rel["r_info_type"] in (21, 22):  # GLOB_DAT, JUMP_SLOT
                    sym = dynsym.get_symbol(rel["r_info_sym"])
                    got_relocs[rel["r_offset"]] = sym.name

    # 0x4a6d4 里引用 GOT 的位置
    # ldr r0,[pc,#0x1a8] @0x4a6e2 → literal at (0x4a6e2+4)&~3 + 0x1a8
    for ins_addr, imm in [(0x4a6e2, 0x1a8), (0x4a6f2, 0x19c)]:
        pc = (ins_addr + 4) & ~3
        lit_va = pc + imm
        got_va = struct.unpack("<I", read_va(elf, lit_va, 4))[0]
        # got_va 是 GOT 表项地址，找其符号
        name = got_relocs.get(got_va, got_relocs.get(got_va & 0xFFFFFFF, f"<unknown 0x{got_va:x}>"))
        print(f"ins@0x{ins_addr:x} imm={imm:#x} → GOT项=0x{got_va:x} → 符号={name}")

    # 0x4a894 里引用 GOT 的位置
    for ins_addr, imm in [(0x4a8a2, 0x44), (0x4a8b4, 0x34)]:
        pc = (ins_addr + 4) & ~3
        lit_va = pc + imm
        got_va = struct.unpack("<I", read_va(elf, lit_va, 4))[0]
        name = got_relocs.get(got_va, f"<unknown 0x{got_va:x}>")
        print(f"ins@0x{ins_addr:x} imm={imm:#x} → GOT项=0x{got_va:x} → 符号={name}")

    # 0x4a8f0
    for ins_addr, imm in [(0x4a8fe, 0x290), (0x4a90a, 0x288)]:
        pc = (ins_addr + 4) & ~3
        lit_va = pc + imm
        got_va = struct.unpack("<I", read_va(elf, lit_va, 4))[0]
        name = got_relocs.get(got_va, f"<unknown 0x{got_va:x}>")
        print(f"ins@0x{ins_addr:x} imm={imm:#x} → GOT项=0x{got_va:x} → 符号={name}")

    # 反汇编 0x42db6
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("\n=== 0x42db6 ===")
    code = read_va(elf, 0x42db6, 0x40)
    for ins in md.disasm(code, 0x42db6):
        print(f"0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")
