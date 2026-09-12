import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

def read_ptr(addr):
    return struct.unpack_from("<I", data, addr)[0]

def read_cstr(addr):
    if addr >= len(data):
        return "<oob>"
    end = data.find(b"\x00", addr)
    if end < 0:
        end = len(data)
    return data[addr:end].decode("utf-8", "replace")

# literal pool 在 0x41bc8 ~ 0x41bd8
for addr in [0x41bc8, 0x41bcc, 0x41bd0, 0x41bd4, 0x41bd8]:
    v = read_ptr(addr)
    print("0x%x = 0x%x" % (addr, v), end="")
    if 0x3c060 <= v <= 0x40c24:
        print("  -> str: %r" % read_cstr(v))
    elif 0x40c28 <= v <= 0x7a528:
        print("  -> fn (text)")
    else:
        print("")
