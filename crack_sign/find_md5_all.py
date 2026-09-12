from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"
TARGET = 0x43338

with open(SO, "rb") as f:
    elf = ELFFile(f)
    text = elf.get_section_by_name(".text")
    data = text.data()
    base = text['sh_addr']
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    insns = list(md.disasm(data, base))
    for i, ins in enumerate(insns):
        # bl 直接调用
        if ins.mnemonic == "bl" and ins.op_str.startswith("#0x"):
            t = int(ins.op_str[1:], 16)
            if t & ~1 == TARGET or t == TARGET:
                print(f"bl @0x{ins.address:08x} -> 0x{t:x}")
        # adr 加载地址
        if ins.mnemonic == "adr" and TARGET == ins.address + int(ins.op_str[1:], 16):
            print(f"adr @0x{ins.address:08x}")
