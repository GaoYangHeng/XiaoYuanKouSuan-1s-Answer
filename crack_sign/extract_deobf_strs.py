from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
import re

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

    targets = [0x453fc, 0x455c0, 0x45660, 0x45680, 0x45f00, 0x46060,
               0x46334, 0x46460, 0x46dec, 0x46ee0, 0x47124, 0x471dc,
               0x45850, 0x45c2c, 0x47454, 0x47640]
    for base in targets:
        code = read_va(elf, base, 0x140)
        chars = []
        for ins in mdt.disasm(code, base):
            if ins.mnemonic in ("movs", "mov.w") and "r1" in ins.op_str and "#" in ins.op_str:
                m = re.search(r"#(0x[0-9a-f]+)", ins.op_str)
                if m:
                    c = int(m.group(1), 16)
                    if 0 < c < 0x100:
                        chars.append(c)
        s = "".join(chr(c) for c in chars)
        if s:
            print(f"0x{base:08x}: \"{s}\"")
