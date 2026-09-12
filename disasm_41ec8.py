from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# 反汇编 0x41ec8 完整（获取 PackageManager/签名）
print("=== 0x41ec8 full ===")
code = data[0x41ec8:0x41f7c]
for insn in md.disasm(code, 0x41ec8):
    ops = insn.op_str
    print("0x%x: %-8s %s" % (insn.address, insn.mnemonic, ops))
    if insn.mnemonic.startswith("pop"):
        break
