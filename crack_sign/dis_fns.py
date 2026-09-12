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
    return d.split(b"\x00")[0].decode("utf-8", "replace")

with open(SO, "rb") as f:
    elf = ELFFile(f)
    print("=== 静态字符串 @0x3d4ff (pc_rel_2, Entry0.sig) ===")
    print(repr(cstr(elf, 0x3d4ff)))

    for name, va in [("fn_A=0x414e6", 0x414e6), ("fn_B=0x40c6a", 0x40c6a)]:
        print(f"\n=== {name} 反汇编 (Thumb) ===")
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        code = read_va(elf, va, 0x200)
        cnt = 0
        for ins in md.disasm(code, va):
            print(f"0x{ins.address:08x}: {ins.mnemonic:12s} {ins.op_str}")
            cnt += 1
            if cnt > 60:
                print("...(截断)")
                break
