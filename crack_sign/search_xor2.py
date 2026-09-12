import itertools

data = open(r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so", "rb").read()

targets = [b"getString", b"android_id", b"ContentResolver", b"getContentResolver", b"Settings$Secure"]

# 从 0x4a6d4/0x4a894/0x4a8f0 观察到的常量
consts = [0x6a, 0x61, 0x76, 0x6d, 0x50, 0x4d, 0x4c, 0x61, 0x6e]

# 尝试用这些常量（及它们的各种顺序）作为 XOR 密钥
keys = [bytes(consts)]

for t in targets:
    for key in keys:
        # 重复密钥到目标长度
        k = (key * ((len(t) + len(key) - 1) // len(key)))[:len(t)]
        enc = bytes(a ^ b for a, b in zip(t, k))
        if enc in data:
            print(f"[命中] {t!r} XOR key={key!r} -> enc={enc.hex()}")
            break
    else:
        print(f"[未命中] {t!r}")

# 也尝试直接搜索这 9 字节常量序列本身是否在 .rodata 中
seq = bytes(consts)
print("常量序列 javamPMLan 在 SO 中:", seq in data)
