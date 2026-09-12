from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

with open(SO, "rb") as f:
    elf = ELFFile(f)
    text = elf.get_section_by_name(".text")
    code = text.data()
    base = text['sh_addr']
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    for ins in md.disasm(code, base):
        # 找 BL/BLX 到 0x43338（MD5 入口）
        if ins.mnemonic in ("bl", "blx", "b.w"):
            op = ins.op_str.strip('#')
            try:
                tgt = int(op, 16)
            except Exception:
                continue
            if tgt == 0x43338 or tgt == 0x43339:
                print(f"0x{ins.address:08x}: {ins.mnemonic} {ins.op_str}  -> MD5 0x43338")
