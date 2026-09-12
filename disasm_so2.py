from capstone import *
from capstone.arm import *
import struct

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump\lib_armeabi-v7a_libRequestEncoder.so"
data = open(SO, "rb").read()

def disasm_thumb(start, length):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    code = data[start:start+length]
    for insn in md.disasm(code, start):
        print("0x%x: %s %s" % (insn.address, insn.mnemonic, insn.op_str))

def read_str(addr):
    if addr >= len(data):
        return None
    end = data.find(b"\x00", addr)
    if end < 0:
        end = len(data)
    return data[addr:end].decode("utf-8", "replace")

def read_ptr(addr):
    if addr + 4 > len(data):
        return None
    return struct.unpack_from("<I", data, addr)[0]

# 0x41be4 加载 PC+0x40 的指针，PC=0x41be8, +0x40=0x41c28
print("=== 0x41c28 ptr ===")
p = read_ptr(0x41c28)
print("ptr -> 0x%x" % p if p else "none")
if p:
    print("str:", read_str(p))

# RegisterNatives 在 0x41aec
print("\n=== func @ 0x41aec ===")
disasm_thumb(0x41aec, 0x60)

# 找方法注册表：通常 {name, sig, fnptr} 三连
# 搜索签名字符串 (Ljava/lang/String;Ljava/lang/String;I)Ljava/lang/String;
print("\n=== search sig string ===")
sig = b"(Ljava/lang/String;Ljava/lang/String;I)Ljava/lang/String;"
idx = data.find(sig)
print("sig offset:", hex(idx) if idx >= 0 else "not found")

# 找方法名（在签名附近）
if idx >= 0:
    for off in range(idx-64, idx):
        pass
    # 往前找方法名字符串
    for off in range(idx-128, idx):
        if data[off] == 0:
            continue
        s = read_str(off)
        if s and 4 <= len(s) <= 32 and all(32 <= ord(c) < 127 for c in s):
            print("near str @0x%x: %r" % (off, s))
