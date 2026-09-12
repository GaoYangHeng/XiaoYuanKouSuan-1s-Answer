import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

# 已知签名字符串偏移
sig = b"(Ljava/lang/String;Ljava/lang/String;I)Ljava/lang/String;"
sig_off = data.find(sig)
print("sig off:", hex(sig_off))

# 在签名附近搜索方法名（zcvsd1wr2t / sdwioxccsd）
for name in [b"zcvsd1wr2t", b"sdwioxccsd", b"RequestEncoder", b"e"]:
    off = data.find(name)
    print(name, "->", hex(off) if off >= 0 else "not found")

# 搜索所有指向 sig_off 的指针（方法表里 sig 字段）
print("\n=== pointers to sig string ===")
for i in range(0, len(data) - 4, 4):
    v = struct.unpack_from("<I", data, i)[0]
    if v == sig_off:
        print("ptr @0x%x -> sig" % i)

# 在 .rodata 找方法表：连续 3 个指针，其中 sig 指向 sig_off
# 方法表项 {name, sig, fn}
for i in range(0, len(data) - 12, 4):
    p0, p1, p2 = struct.unpack_from("<III", data, i)
    if p1 == sig_off:
        print("method table @0x%x: name=0x%x sig=0x%x fn=0x%x" % (i, p0, p1, p2))
        if p0 < len(data):
            end = data.find(b"\x00", p0)
            print("   name str:", data[p0:end])
        print("   fn addr: 0x%x" % (p2 & ~1))
