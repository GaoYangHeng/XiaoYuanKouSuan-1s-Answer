from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

with open(SO, "rb") as f:
    elf = ELFFile(f)
    text = elf.get_section_by_name(".text")
    data = text.data()
    base = text['sh_addr']
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    # 搜索 BL 到 0x43338（MD5）
    for ins in md.disasm(data, base):
        if ins.mnemonic == "bl" and ins.op_str.startswith("#0x"):
            tgt = int(ins.op_str[1:], 16)
            if tgt in (0x43338, 0x43b8c):
                print(f"0x{ins.address:08x}: bl 0x{tgt:x}  <- MD5 调用点")
