from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# 反汇编 0x41aec ~ 0x41bdc（JNI_OnLoad 调用的函数，疑似 RegisterNatives 封装）
code = data[0x41aec:0x41bdc]
for insn in md.disasm(code, 0x41aec):
    ops = insn.op_str
    print("0x%x: %-8s %s" % (insn.address, insn.mnemonic, ops))
