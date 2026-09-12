from capstone import *
from capstone.arm import *
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# .text 段 addr==offset: 0x40c28 ~ 0x7a528
# MD5 常量 0x67452301 在 0x43388 (literal pool)
# 找引用 0x43388 的 LDR 指令（PC 相对）
refs = []
code = data[0x40c28:0x7a528]
for insn in md.disasm(code, 0x40c28):
    if insn.mnemonic.startswith("ldr"):
        for op in insn.operands:
            if op.type == ARM_OP_MEM and op.mem.base == ARM_REG_PC:
                addr = (insn.address + 4) & ~3
                target = addr + op.mem.disp
                if 0x43380 <= target <= 0x439a0:
                    refs.append((insn.address, target))

print("refs to MD5 const/literal region:", len(refs))
for a, t in refs:
    print("  0x%x -> 0x%x" % (a, t))

# 找 refs 所在函数（往上找 push）
funcs = set()
for a, t in refs:
    start = max(0x40c28, a - 0x400)
    window = data[start:a]
    win_md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    last_push = start
    for insn in win_md.disasm(window, start):
        if insn.mnemonic == "push":
            last_push = insn.address
    funcs.add(last_push)

print("\nfuncs containing MD5 refs:")
for f in sorted(funcs):
    print("  0x%x" % f)

# 也找调用这些函数的调用者（找 BL 指令）
callers = set()
for f in sorted(funcs):
    for insn in md.disasm(code, 0x40c28):
        if insn.mnemonic == "bl" and insn.operands:
            tgt = insn.operands[0].imm
            if abs(tgt - f) < 0x100:
                callers.add(insn.address)

print("\ncallers of MD5 funcs:")
for c in sorted(callers):
    print("  0x%x" % c)
