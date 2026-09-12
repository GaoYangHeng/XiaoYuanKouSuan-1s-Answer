from elftools.elf.elffile import ELFFile
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec['sh_addr']
        s = sec['sh_size']
        if a <= va < a + s:
            off = va - a
            return sec.data()[off:off+size]
    return None

def word_at(elf, va):
    d = read_va(elf, va, 4)
    return struct.unpack("<I", d)[0] if d else None

def align4(x):
    return x & ~3

# 三处 pc-relative 地址解析
# ldr r0,[pc,#imm] 指令在 A，字面量地址 = align(A+4,4)+imm
# add r0,pc 指令在 A+2，此时 pc = A+2+4 = A+6
entries = [
    ("pc_rel_1 (sp+0x3c)", 0x41b1c, 0xa8),
    ("pc_rel_2 (sp+0x38)", 0x41b22, 0xa8),
    ("pc_rel_3 (sp+0x48)", 0x41b28, 0xa4),
]

with open(SO, "rb") as f:
    elf = ELFFile(f)
    for name, instr_addr, imm in entries:
        lit_addr = align4(instr_addr + 4) + imm
        val = word_at(elf, lit_addr)
        final = instr_addr + 6 + val
        print(f"{name}: instr=0x{instr_addr:x} lit=0x{lit_addr:x} word=0x{val:x} -> addr=0x{final:08x}")
        # 尝试读取该地址处内容
        d = read_va(elf, final, 24)
        if d:
            try:
                txt = d.split(b"\x00")[0].decode()
                if txt.isprintable() and len(txt) > 1:
                    print(f"    -> 字符串: {txt!r}")
            except Exception:
                pass
            print(f"    -> 字节: {d[:12].hex()}")
