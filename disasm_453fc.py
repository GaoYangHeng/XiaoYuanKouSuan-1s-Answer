from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# 反汇编 0x453fc（method1 调用的函数，可能读签名）
print("=== func @0x453fc ===")
code = data[0x453fc:0x453fc + 0x200]
for insn in md.disasm(code, 0x453fc):
    print("0x%x: %-8s %s" % (insn.address, insn.mnemonic, insn.op_str))
    if insn.mnemonic.startswith("pop"):
        break
