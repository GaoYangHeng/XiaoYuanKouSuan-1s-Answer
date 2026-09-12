import struct
from capstone import *
from capstone.arm import *

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

def calc_literal(insn_addr, imm):
    # Thumb ldr literal: addr = Align(PC,4) + imm; PC = insn_addr + 4
    pc = insn_addr + 4
    addr = (pc & ~3) + imm
    return struct.unpack_from("<I", data, addr)[0]

def add_pc(val, insn_addr):
    # add r0, pc: PC = insn_addr + 4
    return (val + insn_addr + 4) & 0xffffffff

# 方法1 fn: 0x41b1c ldr pc,#0xa8 -> 0x41bc8; add pc @0x41b1e
v1 = calc_literal(0x41b1c, 0xa8)
a1 = add_pc(v1, 0x41b1e)
print("method1 fn: lit=0x%x -> addr=0x%x (thumb entry 0x%x)" % (v1, a1, a1 & ~1))

# 方法1 sig: 0x41b22 ldr pc,#0xa8 -> 0x41bcc; add pc @0x41b24
v2 = calc_literal(0x41b22, 0xa8)
a2 = add_pc(v2, 0x41b24)
print("method1 sig: lit=0x%x -> addr=0x%x" % (v2, a2))
# 读 a2 字符串
end = data.find(b"\x00", a2)
print("  sig str:", data[a2:end])

# 方法2 fn: 0x41b28 ldr pc,#0xa4 -> 0x41bd0; add pc @0x41b2a
v3 = calc_literal(0x41b28, 0xa4)
a3 = add_pc(v3, 0x41b2a)
print("method2 fn: lit=0x%x -> addr=0x%x (thumb entry 0x%x)" % (v3, a3, a3 & ~1))

# 反汇编两个函数
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

for label, entry in [("method1 (zcvsd1wr2t)", a1 & ~1), ("method2 (sdwioxccsd)", a3 & ~1)]:
    print("\n=== %s @0x%x ===" % (label, entry))
    code = data[entry:entry + 0x180]
    for insn in md.disasm(code, entry):
        print("0x%x: %-8s %s" % (insn.address, insn.mnemonic, insn.op_str))
        if insn.mnemonic.startswith("pop"):
            break
