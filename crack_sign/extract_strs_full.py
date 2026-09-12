from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
import re

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

e = ELFFile(open(SO, "rb"))
t = e.get_section_by_name(".text")
base = t["sh_addr"]
d = t.data()
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)

for fn in [0x47454, 0x47640, 0x44280]:
    chars = []
    for ins in md.disasm(d[fn - base: fn - base + 0x600], fn):
        if ins.mnemonic in ("movs", "mov.w") and "r1" in ins.op_str and "#" in ins.op_str:
            m = re.search(r"#(0x[0-9a-f]+)", ins.op_str)
            if m:
                v = int(m.group(1), 16)
                if 0x20 <= v < 0x7f:
                    chars.append(chr(v))
    s = "".join(chars)
    print(f"0x{fn:x} ({len(s)} 字符): \"{s}\"")
