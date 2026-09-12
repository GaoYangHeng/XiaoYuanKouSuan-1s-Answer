data = open(r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so", "rb").read()

targets = [b"android_id", b"getString", b"ContentResolver", b"android/content/ContentResolver",
           b"Settings$Secure", b"getContentResolver"]

print("=== 明文搜索 ===")
for t in targets:
    print(t, "->", t in data)

print("=== 单字节 XOR 搜索 ===")
for t in targets:
    found = []
    for k in range(256):
        enc = bytes(b ^ k for b in t)
        if enc in data:
            found.append(k)
    print(t, "-> XOR keys:", [hex(k) for k in found] if found else "无")
