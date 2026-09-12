from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

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

    # abort 调用点 0x4293d 附近
    print("=== 0x428f0 ~ 0x42960 (abort LR=0x4293d) ===")
    code = read_va(elf, 0x428f0, 0x70)
    for ins in mdt.disasm(code, 0x428f0):
        mark = "  <-- abort LR" if ins.address == 0x4293d else ""
        print(f"  0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}{mark}")

    # r3=0x4420a 指向的位置
    print("\n=== 0x441f0 ~ 0x44230 (r3=0x4420a) ===")
    code = read_va(elf, 0x441f0, 0x40)
    for ins in mdt.disasm(code, 0x441f0):
        print(f"  0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}")

    # 0x4afc6 所在函数
    print("\n=== 0x4afa0 ~ 0x4b020 (0x4afc6 ctor2) ===")
    code = read_va(elf, 0x4afa0, 0x80)
    for ins in mdt.disasm(code, 0x4afa0):
        mark = "  <-- hook 0x4afc6" if ins.address == 0x4afc6 else ""
        print(f"  0x{ins.address:08x}: {ins.mnemonic:10s} {ins.op_str}{mark}")
