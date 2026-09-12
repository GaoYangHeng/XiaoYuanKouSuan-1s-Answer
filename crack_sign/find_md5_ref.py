from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

TARGET = 0x43338

with open(SO, "rb") as f:
    elf = ELFFile(f)
    text = elf.get_section_by_name(".text")
    data = text.data()
    base = text['sh_addr']
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    insns = list(md.disasm(data, base))
    # 找 movw/movt 加载 TARGET
    for i, ins in enumerate(insns):
        if ins.mnemonic == "movw" and ins.op_str.startswith("#"):
            imm = int(ins.op_str[1:], 16)
            if imm == (TARGET & 0xFFFF):
                # 看下一条是不是 movt
                if i + 1 < len(insns) and insns[i+1].mnemonic == "movt":
                    imm2 = int(insns[i+1].op_str[1:], 16)
                    if imm2 == ((TARGET >> 16) & 0xFFFF):
                        print(f"movw/movt 加载 0x{TARGET:x} @ 0x{ins.address:08x}")
