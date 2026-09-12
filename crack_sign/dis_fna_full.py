from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec['sh_addr']; s = sec['sh_size']
        if a <= va < a + s:
            return sec.data()[va-a:va-a+size]
    return None

def cstr(elf, va, maxlen=200):
    d = read_va(elf, va, maxlen)
    if not d:
        return None
    try:
        return d.split(b"\x00")[0].decode("utf-8", "replace")
    except Exception:
        return None

with open(SO, "rb") as f:
    elf = ELFFile(f)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    code = read_va(elf, 0x414e6, 0x380)
    for ins in md.disasm(code, 0x414e6):
        extra = ""
        # 解析 pc 相对字符串
        if ins.mnemonic.startswith("bl") and ins.op_str.startswith("#0x"):
            try:
                tgt = int(ins.op_str[1:], 16)
                s = cstr(elf, tgt & ~1 if (tgt & 1) else tgt)
                if s and s.isprintable():
                    extra = f"  ;; str={s!r}"
            except Exception:
                pass
        print(f"0x{ins.address:08x}: {ins.mnemonic:12s} {ins.op_str}{extra}")
