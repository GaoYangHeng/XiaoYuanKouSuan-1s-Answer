from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

# 签名字符串 vaddr（.rodata addr==off，签名字符串在 0x3d4ff）
SIG_VADDR = 0x3d4ff

with open(SO, "rb") as f:
    elf = ELFFile(f)
    for sec in elf.iter_sections():
        if isinstance(sec, RelocationSection):
            for rel in sec.iter_relocations():
                r_off = rel['r_offset']
                # R_ARM_RELATIVE = 23；addend 从符号或 r_offset 处读取
                rtype = rel['r_info_type']
                sym = rel['r_info_sym']
                addend = None
                if sym == 0:
                    # R_ARM_RELATIVE: addend 存在 r_offset 处
                    if r_off + 4 <= len(data):
                        addend = struct.unpack_from("<I", data, r_off)[0]
                if addend == SIG_VADDR or (sym and elf.get_symbol(sym)):
                    pass
                # 打印所有 R_ARM_RELATIVE 且 addend 在 rodata 字符串区的
                if addend and 0x3c000 <= addend <= 0x40c24:
                    print("reloc @0x%x type=%d addend=0x%x" % (r_off, rtype, addend))
