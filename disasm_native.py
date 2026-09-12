from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# 反汇编 native 函数 0x40c6d（可能 zcvsd1wr2t 或 sdwioxccsd）
# 先反汇编一段，找函数边界（push 到 pop）
code = data[0x40c6d:0x40c6d + 0x400]
for insn in md.disasm(code, 0x40c6d):
    ops = insn.op_str
    print("0x%x: %-8s %s" % (insn.address, insn.mnemonic, ops))
    if insn.mnemonic.startswith("pop"):
        break
