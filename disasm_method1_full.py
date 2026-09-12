from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# 反汇编 method1 完整（0x414e8 到 0x41a62，之前看到 bne.w #0x41a62）
code = data[0x4157a:0x41a62]
for insn in md.disasm(code, 0x4157a):
    print("0x%x: %-8s %s" % (insn.address, insn.mnemonic, insn.op_str))
