from elftools.elf.elffile import ELFFile
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec['sh_addr']; s = sec['sh_size']
        if a <= va < a + s:
            return sec.data()[va-a:va-a+size]
    return None

e = ELFFile(open(SO, "rb"))

# 解析 0x44b60 里的 PC 相对调用
# ldr rX, [pc, #imm] 的 PC = (ins_addr+4)&~3，字面量 = PC + imm
# add rX, pc 的 PC = add_addr + 4
# 目标 = delta(符号扩展) + (add_addr + 4)
for ldr_addr, add_addr, imm in [(0x44b90, 0x44b94, 0xb8), (0x44ba0, 0x44ba4, 0xb4), (0x44bb0, 0x44bb4, 0xa8), (0x44bc0, 0x44bc4, 0x94)]:
    pc = (ldr_addr + 4) & ~3
    lit = pc + imm
    delta = struct.unpack("<i", read_va(e, lit, 4))[0]  # 有符号
    target = (add_addr + 4) + delta
    print(f"ldr@0x{ldr_addr:x} lit@0x{lit:x} delta={delta} -> 目标函数 0x{target:x}")
