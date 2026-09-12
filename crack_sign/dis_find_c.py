from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec["sh_addr"]; s = sec["sh_size"]
        if a <= va < a + s:
            return sec.data()[va - a: va - a + size]
    return None

with open(SO, "rb") as f:
    elf = ELFFile(f)
    mdt = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    start, size = 0x416c0, 0x1c0
    code = read_va(elf, start, size)
    for ins in mdt.disasm(code, start):
        line = f"0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}"
        # 标记写 sp 的指令
        if ins.mnemonic.startswith("str") and "sp" in ins.op_str:
            line += "   ; WRITE-SP"
        print(line)
