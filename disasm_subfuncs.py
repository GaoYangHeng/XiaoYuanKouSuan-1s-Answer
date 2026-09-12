from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# 反汇编 0x41e74 和 0x41ec8，提取 movs r1 字符 + 看 JNI 调用
for label, addr in [("func 0x41e74", 0x41e74), ("func 0x41ec8", 0x41ec8)]:
    print("=== %s ===" % label)
    chars = []
    code = data[addr:addr + 0x120]
    for insn in md.disasm(code, addr):
        # 提取 movs r1, #imm 字符
        if insn.mnemonic == "movs" and insn.operands:
            o0, o1 = insn.operands[0], insn.operands[1]
            if o0.type == ARM_OP_REG and o0.reg == ARM_REG_R1 and o1.type == ARM_OP_IMM:
                if 32 <= o1.imm < 127:
                    chars.append(chr(o1.imm))
        # 打印 bl/blx 调用（可能读签名）
        if insn.mnemonic in ("bl", "blx"):
            print("  0x%x: %s %s" % (insn.address, insn.mnemonic, insn.op_str))
        if insn.mnemonic.startswith("pop"):
            break
    if chars:
        print("  字符序列:", repr("".join(chars)))
    print()
