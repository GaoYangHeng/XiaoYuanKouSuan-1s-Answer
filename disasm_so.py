from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"

data = open(SO, "rb").read()

def disasm_thumb(start, length):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    code = data[start:start+length]
    for insn in md.disasm(code, start):
        print("0x%x: %s %s" % (insn.address, insn.mnemonic, insn.op_str))

# JNI_OnLoad at 0x41bdc
print("=== JNI_OnLoad (thumb) ===")
disasm_thumb(0x41bdc, 0x80)
