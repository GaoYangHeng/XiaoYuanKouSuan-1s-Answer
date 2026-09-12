from elftools.elf.elffile import ELFFile
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

def read_va(elf, va, size):
    for sec in elf.iter_sections():
        a = sec['sh_addr']
        s = sec['sh_size']
        if a <= va < a + s:
            off = va - a
            return sec.data()[off:off+size]
    return None

e = ELFFile(open(SO, "rb"))

# 解析 0x41a62 的 GOT 访问：ldr r0, [pc, #0x80] @ 0x41a62
# Thumb ldr 字面量地址 = Align(PC,4) + imm，PC = 指令地址+4
pc = (0x41a62 + 4) & ~3
lit = pc + 0x80
delta = struct.unpack("<I", read_va(e, lit, 4))[0]
print(f"字面量 @0x{lit:x} = 0x{delta:x}")
# add r0, pc @ 0x41a6c: r0 = (0x41a6c+4) + delta
got_slot = (0x41a6c + 4) + delta
print(f"GOT 槽 @0x{got_slot:x}")
got_val = struct.unpack("<I", read_va(e, got_slot, 4))[0]
print(f"GOT 值 = 0x{got_val:x}")

# 全局对象 + 8 的 string
obj = got_val
print(f"全局对象 @0x{obj:x}，+8 = 0x{obj+8:x}")
data = read_va(e, obj + 8, 32)
print(f"[全局对象+8] 32字节: {data.hex()}")

# 解析 std::string（SBO）
b0 = data[0]
if b0 & 1:
    ln = struct.unpack("<I", data[4:8])[0]
    ptr = struct.unpack("<I", data[8:12])[0]
else:
    ln = b0 >> 1
    ptr = obj + 8 + 1
s = read_va(e, ptr, ln) if ln else b""
print(f"全局 string 长度={ln} 内容={s!r}")
