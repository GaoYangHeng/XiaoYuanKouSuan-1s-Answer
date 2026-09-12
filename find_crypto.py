import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

# MD5 初始常量（little-endian 4字节）
md5_consts = [0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476]
# SHA1 初始常量
sha1_consts = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0]
# SHA256 初始常量
sha256_consts = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]

def search_consts(consts, name):
    found = []
    for c in consts:
        pat = struct.pack("<I", c)
        offs = []
        start = 0
        while True:
            idx = data.find(pat, start)
            if idx < 0:
                break
            offs.append(idx)
            start = idx + 1
        found.append(offs)
        if offs:
            print("%s const 0x%08x found at: %s" % (name, c, [hex(o) for o in offs[:5]]))
    return found

print("=== MD5 ===")
search_consts(md5_consts, "MD5")
print("=== SHA1 ===")
search_consts(sha1_consts, "SHA1")
print("=== SHA256 ===")
search_consts(sha256_consts, "SHA256")

# 也搜索 base64 表
b64 = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
off = data.find(b64)
print("base64 table:", hex(off) if off >= 0 else "not found")

# 搜索 MD5 K 表的一部分（0xd76aa478 是 MD5 T[1]）
pat = struct.pack("<I", 0xd76aa478)
print("MD5 T[1]=0xd76aa478:", hex(data.find(pat)) if data.find(pat) >= 0 else "not found")
