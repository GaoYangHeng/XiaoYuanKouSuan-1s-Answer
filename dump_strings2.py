SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

# .rodata addr==off (0x3c060 ~ 0x40c24)
def read_cstr(addr):
    if addr >= len(data):
        return None
    end = data.find(b"\x00", addr)
    if end < 0:
        end = len(data)
    return data[addr:end].decode("utf-8", "replace")

# 签名字符串
print("sig @0x3d4ff:", repr(read_cstr(0x3d4ff)))

# 读所有重定位 addend 指向的字符串
addrs = [0x3fd71, 0x3fe3e, 0x3ff27, 0x400f0, 0x402dc, 0x407af, 0x407ea,
         0x4081a, 0x4084c, 0x3d6f4, 0x3d567, 0x3d35d, 0x3c8df, 0x3d8bc,
         0x3cd60, 0x3ce8e, 0x3cd67, 0x3d089]
print("\n=== strings at reloc addends ===")
for a in addrs:
    s = read_cstr(a)
    print("0x%x: %r" % (a, s))

# 在 0x3d4ff 附近搜索方法名（前后 256 字节）
print("\n=== strings near sig (0x3d4ff) ===")
for off in range(0x3d400, 0x3d600):
    if data[off] != 0 and (off == 0x3d400 or data[off-1] == 0):
        s = read_cstr(off)
        if s and 3 <= len(s) <= 40 and all(32 <= ord(c) < 127 for c in s):
            print("0x%x: %r" % (off, s))
