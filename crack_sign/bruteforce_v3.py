import hashlib

path = "/leo-game-pk/android/math/pk/match/v2"
key = "wdi4n2t8edr"

samples = [
    ("d9a0ede59cd64436379a3d6e716c3f74", 1788084659),
    ("4d4fb91c395b601b9b61816f16420484", 1788084681),
    ("57e40701ec58b4d9c89f471310ad3270", 1788084809),
    ("296bca5eaca63108fd727d1035173222", 1788084859),
    ("03f6ab5174f50e90bce5645947bf11e6", 1788085018),
]

def md5(s):
    return hashlib.md5(s.encode()).hexdigest()

def make_sign(p, k, minute, delta):
    # p: path 字符串（首字符未修改）
    pm = chr((ord(p[0]) + delta) & 0xFF) + p[1:]
    s = pm + k
    s += md5(s)
    s += pm
    s += md5(s)
    s += str(minute)
    s += md5(s)
    s += k
    return md5(s)

found = False
for use_min in (True, False):
    for delta in range(-256, 256):
        ok = True
        for sign, ts in samples:
            minute = ts // 60 if use_min else ts
            if make_sign(path, key, minute, delta) != sign:
                ok = False
                break
        if ok:
            print(f"[命中] delta={delta} minutes={use_min}")
            found = True
            break
    if found:
        break

if not found:
    print("未命中：delta -256..255，分钟/秒")

# 打印几个参考值
print("\n参考：delta=0, minutes=True, 第一个样本的 sign =", make_sign(path, key, samples[0][1]//60, 0))
print("目标 sign =", samples[0][0])
