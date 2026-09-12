import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

# .text 段 addr==off: 0x40c28 ~ 0x7a528
# .rodata 段 addr==off: 0x3c060 ~ 0x40c24
# .data.rel.ro: vaddr 0x7d470, off 0x7c470 (差 0x1000)

# 搜索 .rodata 和 .data.rel.ro 里指向 .text 的指针（fn 字段）
print("=== pointers to .text (fn fields) in .rodata ===")
for i in range(0x3c060, 0x40c24 - 4, 4):
    v = struct.unpack_from("<I", data, i)[0]
    if 0x40c28 <= v <= 0x7a528:
        print("0x%x -> fn 0x%x" % (i, v))

print("\n=== pointers to .text in .data.rel.ro (file off) ===")
for i in range(0x7c470, 0x7f73c - 4, 4):
    v = struct.unpack_from("<I", data, i)[0]
    if 0x40c28 <= v <= 0x7a528:
        print("0x%x -> fn 0x%x" % (i, v))
