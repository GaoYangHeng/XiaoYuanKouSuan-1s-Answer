from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

def extract_chars(addr, length=0x200):
    chars = []
    code = data[addr:addr+length]
    for insn in md.disasm(code, addr):
        if insn.mnemonic == "movs" and insn.operands:
            o0, o1 = insn.operands[0], insn.operands[1]
            if o0.type == ARM_OP_REG and o0.reg == ARM_REG_R1 and o1.type == ARM_OP_IMM:
                if 32 <= o1.imm < 127:
                    chars.append(chr(o1.imm))
    return "".join(chars)

for label, addr in [("0x4502c", 0x4502c), ("0x451f8", 0x451f8), ("0x41fc0", 0x41fc0), ("0x42db6", 0x42db6)]:
    s = extract_chars(addr)
    print("%s: %r" % (label, s))
