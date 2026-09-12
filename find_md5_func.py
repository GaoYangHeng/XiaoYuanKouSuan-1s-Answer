from capstone import *
from capstone.arm import *
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

# MD5 常量在 0x43388，T 表在 0x438a4
# 反汇编 text 段，找引用这些 .rodata 地址的指令（LDR PC 相对）
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# text 段范围（粗略）
TEXT_START = 0x0
TEXT_END = 0x41000

# 收集引用 0x43388 或 0x438a4 的指令地址
refs = []
code = data[TEXT_START:TEXT_END]
for insn in md.disasm(code, TEXT_START):
    # 找 LDR 或 LDR.W 指令
    if insn.mnemonic.startswith("ldr"):
        for op in insn.operands:
            if op.type == ARM_OP_MEM:
                mem = op.mem
                if mem.base == ARM_REG_PC:
                    disp = mem.disp
                    # 计算目标地址
                    addr = (insn.address + 4) & ~3
                    target = addr + disp
                    if 0x43380 <= target <= 0x438c0 or 0x438a0 <= target <= 0x439a0:
                        refs.append((insn.address, target))

print("refs to MD5 consts region:", len(refs))
for a, t in refs[:30]:
    print("  0x%x -> 0x%x" % (a, t))

# 找 refs 所在函数（往上找 push 指令）
funcs = set()
for a, t in refs:
    # 往上找函数边界
    start = max(0, a - 0x200)
    window = data[start:a]
    win_md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    win_md.detail = True
    last_push = start
    for insn in win_md.disasm(window, start):
        if insn.address < a and insn.mnemonic in ("push",):
            last_push = insn.address
    funcs.add(last_push)

print("\nfuncs containing MD5 const refs:")
for f in sorted(funcs):
    print("  0x%x" % f)
