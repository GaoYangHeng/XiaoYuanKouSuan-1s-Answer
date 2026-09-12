from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# 反汇编 0x44280（0x44b60 里 0x44b82 调用，初始化中间字符串）
print("=== 0x44280 ===")
code = data[0x44280:0x44380]
for insn in md.disasm(code, 0x44280):
    print("0x%x: %-8s %s" % (insn.address, insn.mnemonic, insn.op_str))
    if insn.mnemonic.startswith("pop"):
        break
