# -*- coding: utf-8 -*-
# sign 公式终验：用 FENBI 真实流量 + Test signprobe 双组样本验证 4 轮 MD5 结构
import json, hashlib, os

K = "wdi4n2t8edr"

def md5s(s):
    return hashlib.md5(s.encode()).hexdigest()

def make_sign(path, ts, delta=-1):
    P = chr((ord(path[0]) + delta) & 0xFF) + path[1:]
    T = str(ts // 60)
    h1 = md5s(P + K)
    h2 = md5s(P + K + h1 + P)
    h3 = md5s(P + K + h1 + P + h2 + T)
    return md5s(P + K + h1 + P + h2 + T + h3 + K)

# ---- Test 组（signprobe 实机样本，Test 证书）----
tests = [
    (1788059164, "c09aca9582fbe0a788022afbcba3e4af"),
    (1788059228, "95b23547d8c598bc3df4f484620abb49"),
    (1788059354, "a8a69657806a8e639a9c0832225bb405"),
]
tp = "/leo-game-pk/android/math/pk/match/v2"
t_ok = 0
for ts, sig in tests:
    got = make_sign(tp, ts)
    hit = got == sig
    t_ok += hit
    print("TEST", ts, sig, "HIT" if hit else "MISS got=" + got)

# ---- FENBI 组（真实流量 280 样本）----
data = json.load(open(r"f:\traework_main workspace\xiaoyuan-kousuan-re\sign_samples.json", encoding="utf-8"))
ok = bad = 0
misses = []
for s in data:
    sig, tsm, path = s.get("sign") or "", s.get("ts_ms") or "", s.get("path") or ""
    if not sig or not tsm or not path:
        continue
    ts = int(tsm) // 1000
    got = make_sign(path, ts)
    if got == sig:
        ok += 1
    else:
        bad += 1
        misses.append((path, ts, sig, got))

print("\nFENBI ok=%d bad=%d" % (ok, bad))
for m in misses[:8]:
    print("  MISS", m)

# ---- 模拟器黄金点交叉验证（ts=1788059615 → e0302bee...）----
g = make_sign(tp, 1788059615)
print("\n黄金点", g, "HIT" if g == "e0302beeadb745ecbbfeb2e8f86d426d" else "MISS")

print("\n结论:", "公式确认" if (ok > 0 and bad == 0) else ("部分命中" if ok > 0 else "仍有偏差，需进一步分析"))
