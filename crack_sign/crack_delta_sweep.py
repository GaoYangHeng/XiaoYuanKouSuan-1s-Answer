# -*- coding: utf-8 -*-
# 穷举 delta × 分钟桶，验证链结构与真机 sign 的匹配
# 链结构（模拟器 dump 精确复刻）：
#   P' = chr((ord(P[0])+delta)&0xFF) + P[1:]
#   h1 = md5(P'+K)            48B
#   h2 = md5(P'+K+h1+P')      117B
#   h3 = md5(P'+K+h1+P'+h2+T) 157B   T=str(ts//60)
#   sign = md5(P'+K+h1+P'+h2+T+h3+K) 200B
import hashlib

P = b"/leo-game-pk/android/math/pk/match/v2"
K = b"wdi4n2t8edr"

TARGETS = {
    "d9a0ede59cd64436379a3d6e716c3f74": ("zu1-official", 1788084659),
    "c09aca9582fbe0a788022afbcba3e4af": ("zu3-testcert", 1788059164),
}

def chain(delta, minute):
    first = (P[0] + delta) & 0xFF
    Pp = bytes([first]) + P[1:]
    h1 = hashlib.md5(Pp + K).hexdigest().encode()
    h2 = hashlib.md5(Pp + K + h1 + Pp).hexdigest().encode()
    base = Pp + K + h1 + Pp + h2
    T = str(minute).encode()
    h3 = hashlib.md5(base + T).hexdigest().encode()
    return hashlib.md5(base + T + h3 + K).hexdigest()

hits = []
total = 0
for tsign, (tag, ts) in TARGETS.items():
    center = ts // 60
    for delta in range(-128, 128):
        for dmin in range(-61, 62):
            total += 1
            s = chain(delta, center + dmin)
            if s == tsign:
                hits.append((tag, tsign, delta, center + dmin, center + dmin + dmin * 0))
                print(f"[HIT] {tag} sign={tsign} delta={delta} minute={center+dmin} ts≈{(center+dmin)*60}")
                print(f"      偏移: delta={delta}, ts={((center+dmin)*60) - ts}s")
print(f"扫描完成: {total} 次链计算, 命中 {len(hits)}")
if not hits:
    print("全 miss —— P/K/T 结构或 delta 范围假设有误")
