from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"


def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec["sh_addr"]
        s = sec["sh_size"]
        if a <= va < a + s:
            return sec.data()[va - a: va - a + size]
    return None


with open(SO, "rb") as f:
    elf = ELFFile(f)

    # r5: literal@0x4a88c + pc(0x4a6e8) = 0x7c868 ; r6: literal@0x4a88e + pc = 0x7c836
    for name, got_va in [("r5", 0x7c868), ("r6", 0x7c836)]:
        data = read_va(elf, got_va, 4)
        if data is None:
            print(f"{name}: GOT 0x{got_va:x} 不可读")
            continue
        val = struct.unpack("<I", data)[0]
        print(f"{name}: GOT@0x{got_va:x} = 0x{val:x}")
        # 尝试反汇编目标
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        code = read_va(elf, val & ~1, 0x30)
        if code:
            print(f"  反汇编 0x{val & ~1:x}:")
            for ins in md.disasm(code, val & ~1):
                print(f"    0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")
                if ins.address >= (val & ~1) + 0x20:
                    break
