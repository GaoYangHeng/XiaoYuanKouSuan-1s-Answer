from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

with open(SO, "rb") as f:
    elf = ELFFile(f)
    relplt = elf.get_section_by_name(".rel.plt")
    dynsym = elf.get_section_by_name(".dynsym")
    slots = {}
    for rel in relplt.iter_relocations():
        sym = dynsym.get_symbol(rel['r_info_sym'])
        slots[rel['r_offset']] = sym.name

    # 计算 PLT entry -> GOT 槽
    # entry 结构：add ip,pc,#12; add ip,ip,#0x6000; ldr pc,[ip,#imm]!
    # ip_final = (entry+8+12) + 0x6000 + imm = entry + 0x6014 + imm
    # 反汇编找出每个 entry 的 imm
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
    plt = elf.get_section_by_name(".plt")
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    entries = []
    for ins in md.disasm(plt.data(), plt['sh_addr']):
        if ins.mnemonic == "ldr" and "pc" in ins.op_str and "#" in ins.op_str:
            imm = int(ins.op_str.split("#")[1].split("]")[0], 16)
            entry = ins.address - 8  # ldr 在 entry+8
            got_slot = entry + 0x6014 + imm
            name = slots.get(got_slot, "???")
            print(f"PLT 0x{entry:08x} -> GOT 0x{got_slot:08x} = {name}")
