# -*- coding: utf-8 -*-
# v2：反汇编主 sign 函数 0x414e8 起至 0x41b40，追踪 c(r8) 的计算位点
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM
import re
import sys

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

with open(SO, "rb") as f:
    elf = ELFFile(f)
    dynsym = elf.get_section_by_name(".dynsym")
    relplt = elf.get_section_by_name(".rel.plt")
    slots = {}
    for rel in relplt.iter_relocations():
        slots[rel["r_offset"]] = dynsym.get_symbol(rel["r_info_sym"]).name

    def read_va(va, size):
        for sec in elf.iter_sections():
            a = sec["sh_addr"]; s = sec["sh_size"]
            if a <= va < a + s:
                return sec.data()[va - a: va - a + size]
        return None

    def plt_sym(entry):
        mda = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        code = read_va(entry, 12)
        insns = list(mda.disasm(code, entry))
        if len(insns) < 3:
            return None
        m = re.search(r"#(0x[0-9a-f]+)", insns[2].op_str)
        if not m:
            return None
        imm = int(m.group(1), 16)
        got = entry + 0x6014 + imm
        return slots.get(got, f"GOT0x{got:x}")

    mdt = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    lo = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x414e0
    hi = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x41800
    code = read_va(lo, hi - lo)
    for ins in mdt.disasm(code, lo):
        line = f"0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}"
        if ins.mnemonic in ("bl", "blx") and ins.op_str.startswith("#0x"):
            tgt = int(ins.op_str[1:], 16)
            if 0x79000 <= tgt <= 0x7c000:
                line += f"   ; PLT:{plt_sym(tgt)}"
            elif tgt >= 0x40000:
                line += f"   ; FN:{tgt:x}"
        if ins.mnemonic.startswith("ldr") and "pc" in ins.op_str:
            m = re.search(r"#(0x[0-9a-f]+)\]", ins.op_str)
            if m:
                pc = (ins.address + 4) & ~3
                got = pc + int(m.group(1), 16)
                sym = slots.get(got)
                if sym:
                    line += f"   ; ->{sym}"
        print(line)
