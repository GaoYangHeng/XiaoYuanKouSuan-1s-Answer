from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# 反汇编 0x453fc，提取 movs r1, #imm 的字符序列
code = data[0x453fc:0x45600]
chars = []
for insn in md.disasm(code, 0x453fc):
    if insn.mnemonic == "movs" and insn.operands:
        op0, op1 = insn.operands[0], insn.operands[1]
        if op0.type == ARM_OP_REG and op0.reg == ARM_REG_R1:
            if op1.type == ARM_OP_IMM:
                chars.append((insn.address, op1.imm))

s = "".join(chr(c) for _, c in chars if 32 <= c < 127)
print("字符序列:", repr(s))

# 也看 method2 (sdwioxccsd) @0x40c6c 是否类似
print("\n=== method2 chars ===")
code2 = data[0x40c6c:0x40e00]
chars2 = []
for insn in md.disasm(code2, 0x40c6c):
    if insn.mnemonic == "movs" and insn.operands:
        op0, op1 = insn.operands[0], insn.operands[1]
        if op0.type == ARM_OP_REG and op0.reg == ARM_REG_R1:
            if op1.type == ARM_OP_IMM:
                chars2.append((insn.address, op1.imm))
s2 = "".join(chr(c) for _, c in chars2 if 32 <= c < 127)
print("字符序列:", repr(s2))
