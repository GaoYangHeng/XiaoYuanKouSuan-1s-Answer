from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# 反汇编 0x43338 附近（hook.js 声称的 MD5 入口）
print("=== 0x43338 附近 ===")
code = data[0x43300:0x433a0]
for insn in md.disasm(code, 0x43300):
    print("0x%x: %-8s %s" % (insn.address, insn.mnemonic, insn.op_str))
