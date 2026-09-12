# -*- coding: utf-8 -*-
# sign 公式终验 v2：ts 语义修正——verify_capture 5 条样本的 ts 直接取自请求 query 参数（APP 传的，参与签名）
import hashlib

path = "/leo-game-pk/android/math/pk/match/v2"
K = "wdi4n2t8edr"

def md5s(s):
    return hashlib.md5(s.encode()).hexdigest()

def make_sign(p, ts, delta=-1):
    P = chr((ord(p[0]) + delta) & 0xFF) + p[1:]
    T = str(ts // 60)
    h1 = md5s(P + K)
    h2 = md5s(P + K + h1 + P)
    h3 = md5s(P + K + h1 + P + h2 + T)
    return md5s(P + K + h1 + P + h2 + T + h3 + K)

# ---- 组1：FENBI 真机流量黄金样本（ts 来自 query 参数，语义权威）----
fenbi = [
    ("d9a0ede59cd64436379a3d6e716c3f74", 1788084659),
    ("4d4fb91c395b601b9b61816f16420484", 1788084681),
    ("57e40701ec58b4d9c89f471310ad3270", 1788084809),
    ("296bca5eaca63108fd727d1035173222", 1788084859),
    ("03f6ab5174f50e90bce5645947bf11e6", 1788085018),
]
print("=== 组1 FENBI 真机流量（ts 取自 query 参数）===")
ok1 = 0
for sig, ts in fenbi:
    got = make_sign(path, ts)
    hit = got == sig
    ok1 += hit
    print("ts=%d %s got=%s %s" % (ts, sig, got, "HIT" if hit else "MISS"))
print("组1 命中 %d/5" % ok1)

# ts 秒级统一偏移扫描（设备时钟 vs 抓包时钟）
if ok1 < 5:
    for off in range(-180, 181):
        if all(make_sign(path, ts + off) == sig for sig, ts in fenbi):
            print("[统一偏移命中] offset=%d 秒" % off)
            break
    else:
        # 各样本独立偏移
        for sig, ts in fenbi:
            hits = [o for o in range(-600, 601) if make_sign(path, ts + o) == sig]
            print("  样本 %s 独立偏移: %s" % (sig[:8], hits if hits else "无(±600s)"))

# ---- 组2：模拟器黄金点 ----
g = make_sign(path, 1788059615)
print("\n=== 组2 模拟器黄金点 ===")
print("黄金点", g, "HIT" if g == "e0302beeadb745ecbbfeb2e8f86d426d" else "MISS")

# ---- 组3：Test 签名 signprobe 实机样本 ----
tests = [
    (1788059164, "c09aca9582fbe0a788022afbcba3e4af"),
    (1788059228, "95b23547d8c598bc3df4f484620abb49"),
    (1788059354, "a8a69657806a8e639a9c0832225bb405"),
]
print("\n=== 组3 Test 签名实机样本 ===")
ok3 = 0
for ts, sig in tests:
    got = make_sign(path, ts)
    hit = got == sig
    ok3 += hit
    print("ts=%d %s got=%s %s" % (ts, sig, got, "HIT" if hit else "MISS"))
print("组3 命中 %d/3" % ok3)
