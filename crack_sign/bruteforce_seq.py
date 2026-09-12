import hashlib

KEY = "wdi4n2t8edr"
AID = "39c0141952095d9c"
PATH = "/leo-game-pk/android/math/pk/match/v2"
hex1 = hashlib.md5(AID.encode()).hexdigest()

SAMPLES = [
    (1788059164, "7ccaf869bade9bf18c8f0c3e8a034e23"),
    (1788059228, "cfe580fae28fc66c89610b620c815478"),
]

def md5(s):
    return hashlib.md5(s.encode()).hexdigest()

def ts_strs(epoch):
    m = epoch // 60
    return [str(m), hex(m)[2:], hex(m)[2:].upper(), str(epoch), hex(epoch)[2:]]

# 拼接序列模拟（0x44b60）
def build(P, K, T):
    s = P
    s = s + K
    s = s + s          # tmp = s; s += tmp  => 2s
    s = s + P
    s = s + s          # 2s
    s = s + T
    s = s + s          # 2s
    s = s + K
    return s

for epoch, target in SAMPLES:
    hit = None
    for T in ts_strs(epoch):
        # P 可能是 path 或 path+hex1 或 hex1
        for P in [PATH, PATH + hex1, hex1 + PATH, hex1]:
            for K in [KEY, hex1 + KEY, KEY + hex1]:
                cand = build(P, K, T)
                if md5(cand) == target:
                    hit = (P, K, T, cand)
                    break
            if hit: break
        if hit: break
    print(f"[{'命中' if hit else '未命中'}] ts={epoch} {hit!r}")
