# -*- coding: utf-8 -*-
# patch .so：0x41a3e 起 10 字节（mla 4B + muls 2B + mla 4B）→ movs r4,#0 + nop×4
# 效果：delta 恒 0 = 官方真机观测值（P[0] 不变换），改包版走官方签名路径
# 红线：0x41a48 的 ldr r0,[sp,#0x14]（加载 out_delta 指针）必须保留！
#       旧 12 字节版把它 nop 掉后 str r4,[r0] 会用 42d50 返回值当指针 → 真机 SIGSEGV
from elftools.elf.elffile import ELFFile
import shutil

SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"
OUT = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\libRequestEncoder_patched.so"

PATCH_VA = 0x41A3E
PATCH_LEN = 10
# Thumb: movs r4,#0 (2B) + nop (2B) x4；保留 0x41a48 ldr r0,[sp,#0x14] 与 0x41a4a str r4,[r0]
NEW = bytes([0x00, 0x24] + [0x00, 0xBF] * 4)


def va_to_off(elf, va):
    for seg in elf.iter_segments():
        if seg["p_type"] == "PT_LOAD":
            v = seg["p_vaddr"]
            if v <= va < v + seg["p_filesz"]:
                return va - v + seg["p_offset"]
    return None


with open(SO, "rb") as f:
    raw = bytearray(f.read())

elf = ELFFile(open(SO, "rb"))
off = va_to_off(elf, PATCH_VA)
print(f"VA 0x{PATCH_VA:x} -> file offset 0x{off:x}")

old = bytes(raw[off:off + PATCH_LEN])
print(f"原 {PATCH_LEN} 字节:", old.hex(" "))
print("原指令应为 mla/muls/mla (mla 4B + muls 2B + mla 4B)，0x41a48 ldr 保留")

if old == NEW:
    print("已是 patched 状态，跳过")
else:
    raw[off:off + PATCH_LEN] = NEW
    with open(OUT, "wb") as f:
        f.write(bytes(raw))
    print(f"已写入: {OUT}")
    # 复读验证
    with open(OUT, "rb") as f:
        chk = f.read()[off:off + PATCH_LEN]
    print(f"写入后 {PATCH_LEN} 字节:", chk.hex(" "))
    assert chk == NEW, "验证失败！"
    print("✔ patch 验证通过")
