from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from elftools.elf.sections import SymbolTableSection
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
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

    # 1. 列出包含 0x807xx 的段
    print("=== 包含 0x807a0~0x80840 的段 ===")
    for sec in elf.iter_sections():
        a = sec["sh_addr"]; s = sec["sh_size"]
        if a <= 0x80840 and 0x807a0 < a + s:
            print(f"  {sec.name:20s} addr=0x{a:x} size=0x{s:x}")

    # 2. rel.dyn 符号表
    dynsym = elf.get_section_by_name(".dynsym")
    got_relocs = {}
    for sec in elf.iter_sections():
        if isinstance(sec, RelocationSection):
            for rel in sec.iter_relocations():
                if rel["r_info_type"] in (21, 22, 23):  # GLOB_DAT/JUMP_SLOT/RELATIVE
                    sym = dynsym.get_symbol(rel["r_info_sym"])
                    got_relocs[rel["r_offset"]] = sym.name

    # 3. 反汇编 0x44b60 完整函数
    print("\n=== 0x44b60 完整反汇编 ===")
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    code, sname = read_va(elf, 0x44b60, 0x200)
    for ins in md.disasm(code, 0x44b60):
        line = f"0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}"
        # 对 ldr 字面量解析
        if ins.mnemonic == "ldr" and ins.op_str.startswith("r") and "#" in ins.op_str:
            line += "   ; LDR-literal"
        print(line)

    # 4. 读 GOT 槽值
    print("\n=== GOT/字面量槽值 ===")
    for va in (0x807fe, 0x807a8, 0x8081e, 0x8082c, 0x80830):
        d, sname = read_va(elf, va, 4)
        if d is None:
            print(f"  0x{va:x}: <无法读取>")
            continue
        val = struct.unpack("<I", d)[0]
        sym = got_relocs.get(va, "")
        print(f"  0x{va:x}: 值=0x{val:08x}  符号={sym}  (段 {sname})")

    # 5. 精确重算 0x44b60 的 ldr 字面量（逐条，用 capstone detail）
    print("\n=== 0x44b60 所有 ldr 字面量重算 ===")
    for ins in md.disasm(code, 0x44b60):
        if ins.mnemonic != "ldr":
            continue
        ops = ins.op_str
        if "#0x" not in ops and "pc" not in ops:
            continue
        # 解析 imm
        import re
        m = re.search(r"#(0x[0-9a-f]+)", ops)
        if not m:
            continue
        imm = int(m.group(1), 16)
        pc = (ins.address + 4) & ~3
        lit_va = pc + imm
        d, _ = read_va(elf, lit_va, 4)
        if d is None:
            continue
        lit_val = struct.unpack("<I", d)[0]
        # 目标 = lit_val + (add? 这里无 add 指令信息，直接展示 lit 值)
        print(f"  ldr@0x{ins.address:08x} imm={imm:#x} lit@0x{lit_va:x} = 0x{lit_val:08x}")
