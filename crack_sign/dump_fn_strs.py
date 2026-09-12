from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec['sh_addr']; s = sec['sh_size']
        if a <= va < a + s:
            return sec.data()[va-a:va-a+size]
    return None

def cstr(elf, va, maxlen=300):
    d = read_va(elf, va, maxlen)
    if not d:
        return None
    try:
        return d.split(b"\x00")[0].decode("utf-8", "replace")
    except Exception:
        return None

with open(SO, "rb") as f:
    elf = ELFFile(f)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    code = read_va(elf, 0x414e6, 0x400)
    insns = list(md.disasm(code, 0x414e6))
    for i, ins in enumerate(insns):
        # 匹配 ldr rX, [pc, #0xNN]
        if ins.mnemonic == "ldr" and ins.op_str.startswith("r") and "[pc, #" in ins.op_str:
            reg = ins.op_str.split(",")[0].strip()
            try:
                imm = int(ins.op_str.split("#")[1].split("]")[0], 16)
            except Exception:
                continue
            # 寻找紧邻的 add reg, pc（可能隔了几条）
            for j in range(i+1, min(i+4, len(insns))):
                n = insns[j]
                if n.mnemonic == "add" and n.op_str == f"{reg}, pc":
                    lit = (ins.address + 4) & ~3
                    val = read_va(elf, lit + imm, 4)
                    if val is None:
                        continue
                    word = struct.unpack("<I", val)[0]
                    pc = (n.address + 4) & ~3
                    target = (pc + word) & 0xFFFFFFFF
                    s = cstr(elf, target)
                    if s and len(s) >= 1 and all(32 <= ord(c) < 127 for c in s):
                        print(f"0x{ins.address:08x}: ldr {reg} -> str @0x{target:08x} = {s!r}")
                    else:
                        print(f"0x{ins.address:08x}: ldr {reg} -> addr 0x{target:08x}")
                    break
