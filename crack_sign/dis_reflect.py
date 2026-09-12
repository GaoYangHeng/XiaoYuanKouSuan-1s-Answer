from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec["sh_addr"]; s = sec["sh_size"]
        if a <= va < a + s:
            return sec.data()[va - a: va - a + size], sec.name
    return None, None

def cstr_at(elf, va):
    out = b""
    for i in range(256):
        d, _ = read_va(elf, va + i, 1)
        if d is None or d == b"\x00":
            break
        out += d
    return out

with open(SO, "rb") as f:
    elf = ELFFile(f)
    mdt = Cs(CS_ARCH_ARM, CS_MODE_THUMB)

    # 反汇编反射链区域，解析 ldr 字面量指向的字符串
    start, size = 0x418a0, 0x180
    code, _ = read_va(elf, start, size)
    insns = list(mdt.disasm(code, start))

    # 先收集所有 ldr 字面量地址 -> 值
    lits = {}
    for ins in insns:
        if ins.mnemonic == "ldr" and "pc" in ins.op_str and "#" in ins.op_str:
            import re
            m = re.search(r"#(0x[0-9a-f]+)", ins.op_str)
            if not m:
                continue
            imm = int(m.group(1), 16)
            pc = (ins.address + 4) & ~3
            lit_va = pc + imm
            d, _ = read_va(elf, lit_va, 4)
            if d:
                lits[lit_va] = struct.unpack("<I", d)[0]

    for ins in insns:
        line = f"0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}"
        # 若该指令是 ldr 且字面量指向可读字符串，附加注释
        if ins.mnemonic == "ldr" and "pc" in ins.op_str:
            import re
            m = re.search(r"#(0x[0-9a-f]+)", ins.op_str)
            if m:
                imm = int(m.group(1), 16)
                pc = (ins.address + 4) & ~3
                lit_va = pc + imm
                val = lits.get(lit_va)
                if val is not None:
                    s = cstr_at(elf, val)
                    if s and all(32 <= b < 127 for b in s) and len(s) >= 2:
                        line += f'   ; -> "{s.decode()}"'
        print(line)
