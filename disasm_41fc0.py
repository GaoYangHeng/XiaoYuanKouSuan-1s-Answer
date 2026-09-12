from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# 0x41fc0 是签名读取函数。先看它调用的字符串构建函数，提取类名/方法名/签名
# 提取 0x41fc0 调用的所有 bl 目标
print("=== 0x41fc0 calls ===")
code = data[0x41fc0:0x42100]
for insn in md.disasm(code, 0x41fc0):
    if insn.mnemonic in ("bl", "blx") and insn.operands:
        print("  0x%x: %s %s" % (insn.address, insn.mnemonic, insn.op_str))
    if insn.mnemonic.startswith("pop"):
        break
