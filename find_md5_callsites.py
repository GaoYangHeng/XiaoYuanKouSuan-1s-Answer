from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# MD5 入口 0x43338（Thumb 标志 0x43339）
# 搜索 zcvsd1wr2t（0x414e8~0x41a62）里的 bl 到 MD5 附近
print("=== bl 到 MD5(0x43338) 附近的调用 ===")
code = data[0x414e8:0x41a62]
for insn in md.disasm(code, 0x414e8):
    if insn.mnemonic == "bl" and insn.operands:
        tgt = insn.operands[0].imm
        if 0x43200 <= tgt <= 0x43400:
            print("0x%x: bl 0x%x" % (insn.address, tgt))

# 也搜索 blx 到寄存器（间接调用 MD5）
print("\n=== 所有 bl/blx（zcvsd1wr2t 内）===")
for insn in md.disasm(code, 0x414e8):
    if insn.mnemonic in ("bl", "blx") and insn.operands:
        print("0x%x: %s %s" % (insn.address, insn.mnemonic, insn.op_str))
