import hashlib

path = "/leo-game-pk/android/math/pk/match/v2"
key = "wdi4n2t8edr"
delta = -1

samples = [
    ("d9a0ede59cd64436379a3d6e716c3f74", 1788084659),
    ("4d4fb91c395b601b9b61816f16420484", 1788084681),
    ("57e40701ec58b4d9c89f471310ad3270", 1788084809),
    ("296bca5eaca63108fd727d1035173222", 1788084859),
    ("03f6ab5174f50e90bce5645947bf11e6", 1788085018),
]

def md5(s):
    return hashlib.md5(s.encode()).hexdigest()

def make_sign(p, k, ts, d):
    pm = chr((ord(p[0]) + d) & 0xFF) + p[1:]
    minute = str(ts // 60)
    s = pm + k
    h1 = md5(s)
    s = pm + k + h1 + pm
    h2 = md5(s)
    s = pm + k + h1 + pm + h2 + minute
    h3 = md5(s)
    s = pm + k + h1 + pm + h2 + minute + h3 + k
    return md5(s)

# 直接对比（假设设备时钟 = 电脑时钟）
print("=== 直接对比（ts 精确）===")
match = 0
for sign, ts in samples:
    calc = make_sign(path, key, ts, delta)
    ok = calc == sign
    match += ok
    print(f"ts={ts} 计算={calc} 目标={sign} {'✓' if ok else '✗'}")
print(f"匹配 {match}/5")

# 尝试 ts 偏移（设备时钟和电脑时钟可能差几秒）
print("\n=== 尝试 ts 偏移 ===")
for offset in range(-120, 121):
    ok_all = all(make_sign(path, key, ts + offset, delta) == sign for sign, ts in samples)
    if ok_all:
        print(f"[命中] 偏移 offset={offset} 秒")
        break
else:
    print("未找到统一偏移")
