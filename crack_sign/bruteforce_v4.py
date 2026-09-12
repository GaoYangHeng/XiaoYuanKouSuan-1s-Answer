import hashlib

path = "/leo-game-pk/android/math/pk/match/v2"
key = "wdi4n2t8edr"

# testapp oracle：精确 ts + 精确 sign（设备值 = key.jks 签名）
oracle = [
    ("a23243656982588c5eb30e7b3af3ecb6", 1788059164),
    ("d25bfb9ea38442e48167f50641e56d2c", 1788059228),
    ("b2a25671a2404816a33ee663332cdcfe", 1788059354),
    ("2ef9b4f9f3836a20ceaeef2d03e654b3", 1788059447),
    ("418b7cede5baf80fff3482117407a641", 1788059616),
]

def md5(s):
    return hashlib.md5(s.encode()).hexdigest()

def make_sign(p, k, minute, delta):
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
        for sign, ts in oracle:
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
    print("未命中")

# 打印参考
print("\n参考 delta=0 minutes=True 第一样本:", make_sign(path, key, oracle[0][1]//60, 0))
print("目标:", oracle[0][0])
