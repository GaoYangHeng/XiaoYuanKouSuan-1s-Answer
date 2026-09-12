# 片段：libRequestEncoder.so 的签名校验 patch（关键逻辑）
# 说明：该 .so 会校验应用签名指纹，不匹配则污染 path 首字符 -> 服务端 417。
#       这里把计算污染量的指令改掉，使其恒为 0。
# 已脱敏，仅展示思路与关键常量。

PATCH_OFF = 0x41A3E   # 污染量计算起始（armeabi-v7a）
PATCH_LEN = 10

ORIG = bytes([0x00, 0xfb, 0x04, 0x81, 0x60, 0x43, 0x00, 0xfb, 0x08, 0x14])
# 替换为：movs r4, #0  +  nop x4   ->  污染量恒为 0
PATCH = bytes([0x00, 0x24, 0x00, 0xbf, 0x00, 0xbf, 0x00, 0xbf, 0x00, 0xbf])


def patch(src_path, dst_path):
    data = bytearray(open(src_path, "rb").read())
    assert bytes(data[PATCH_OFF:PATCH_OFF + PATCH_LEN]) == ORIG, "偏移处指令不符，需重新定位"
    data[PATCH_OFF:PATCH_OFF + PATCH_LEN] = PATCH

    # !!! 红线：不要动 0x41A48 / 0x41A4A !!!
    #   0x41A48: 05 98   ldr r0, [sp, #0x14]   <- 加载输出指针
    #   0x41A4A: 04 60   str r4, [r0]          <- 写回污染量
    # 早期 12 字节版本把 ldr 也 nop 掉，导致 str 使用了错误指针 -> 真机 SIGSEGV
    assert bytes(data[0x41A48:0x41A4C]) == bytes([0x05, 0x98, 0x04, 0x60]), "红线指令被破坏"

    open(dst_path, "wb").write(bytes(data))
    print("patched ->", dst_path)


"""
背景：为什么会 417
------------------------------------------------------------------
MD5(0x43338 / 0x43398) -> hex(0x43c04)
  -> 与两枚硬编码 32 位常量比对：
     "9a2806e869bf45f85e601a69f895d213"  @0x47454
     "1dcd877d86d19882d8d055a1a87de93c"  @0x47640        （推测为正版签名指纹）
  -> 不匹配则 A*B != 0 -> delta != 0
  -> 0x41A82: P[0] = (char)(P[0] + delta)                    <- 唯一污染点
  -> 服务端校验 path 失败 -> 417

补充情报：
- 0x42D50 是 std::string::compare 的包装（内部 memcmp + 长度决胜），
  不是 getPackageInfo 封装；全库无 getPackageInfo 字符串。
- .data 首字 G1 @0x82288 = -0x63，静态初值恒通过，切勿改动 .data。
"""
