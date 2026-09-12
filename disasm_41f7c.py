from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# 反汇编 0x41f7c（0x44b60 的调用者）
print("=== 0x41f7c ===")
code = data[0x41f7c:0x42080]
for insn in md.disasm(code, 0x41f7c):
    print("0x%x: %-8s %s" % (insn.address, insn.mnemonic, insn.op_str))
    if insn.mnemonic.startswith("pop"):
        break
