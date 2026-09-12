import hashlib

path = "/leo-game-pk/android/math/pk/match/v2"
key = "wdi4n2t8edr"
delta = -1

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

# 对第一个样本暴力搜索 ts（分钟粒度，±2 小时）
target = "d9a0ede59cd64436379a3d6e716c3f74"
base_ts = 1788084659
found = False
for dt in range(-7200, 7200):
    ts = base_ts + dt
    if make_sign(path, key, ts, delta) == target:
        print(f"[命中] ts={ts} (偏移 {dt} 秒, minute={ts//60})")
        found = True
        break
if not found:
    print("±2 小时内未匹配第一个样本")

# 也尝试 delta 的其他值（0~255）
if not found:
    print("尝试 delta 0..255...")
    for d in range(0, 256):
        for dt in range(-7200, 7200):
            if make_sign(path, key, base_ts + dt, d) == target:
                print(f"[命中] delta={d} ts={base_ts+dt}")
                found = True
                break
        if found:
            break
if not found:
    print("未匹配")
