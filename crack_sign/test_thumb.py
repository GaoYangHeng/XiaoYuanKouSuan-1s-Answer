from unicorn import *
from unicorn.arm_const import *

uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
BASE = 0x1000
uc.mem_map(BASE, 0x2000)

# 实际序言字节（来自 SO @0x414e6）
code = bytes.fromhex(
    "0300f0b503af2de9000fbbb08146dff8e4051e461546784431460022"
)

uc.mem_write(BASE, code)

SP = 0x3000
uc.reg_write(UC_ARM_REG_SP, SP)
uc.reg_write(UC_ARM_REG_R0, 0x1111)

try:
    uc.emu_start(BASE | 1, BASE + len(code))
    print("OK, SP =", hex(uc.reg_read(UC_ARM_REG_SP)))
except UcError as e:
    print("ERR:", e, "PC =", hex(uc.reg_read(UC_ARM_REG_PC)))
