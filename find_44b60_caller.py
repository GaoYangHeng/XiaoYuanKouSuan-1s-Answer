from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# 搜索 .text 里 bl/blx 到 0x44b60 的调用点
print("=== 调用 0x44b60 的位置 ===")
code = data[0x40c28:0x7a528]
for insn in md.disasm(code, 0x40c28):
    if insn.mnemonic in ("bl", "blx"):
        for op in insn.operands:
            if op.type == ARM_OP_IMM:
                if 0x44b50 <= op.imm <= 0x44b70:
                    print("0x%x: %s 0x%x" % (insn.address, insn.mnemonic, op.imm))
