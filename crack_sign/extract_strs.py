from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

e = ELFFile(open(SO, "rb"))
t = e.get_section_by_name(".text")
base = t['sh_addr']
d = t.data()
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

for fn in [0x47454, 0x47640, 0x44280]:
    chars = []
    for i in md.disasm(d[fn-base:fn-base+0x300], fn):
        if i.mnemonic == "movs" and i.op_str.startswith("r1, #"):
            imm = i.op_str.split("#")[1]
            try:
                v = int(imm, 16) if imm.lower().startswith("0x") else int(imm)
            except Exception:
                v = int(imm, 16)
            if 0x20 <= v < 0x7f:
                chars.append(chr(v))
    print(f"0x{fn:x}: \"{''.join(chars)}\"")
