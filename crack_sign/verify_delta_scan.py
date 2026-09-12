# -*- coding: utf-8 -*-
# delta 全范围扫描：FENBI 真机流量组1（ts 权威）× delta -32..32
import hashlib

K = "wdi4n2t8edr"
path = "/leo-game-pk/android/math/pk/match/v2"

fenbi = [
    ("d9a0ede59cd64436379a3d6e716c3f74", 1788084659),
    ("4d4fb91c395b601b9b61816f16420484", 1788084681),
    ("57e40701ec58b4d9c89f471310ad3270", 1788084809),
    ("296bca5eaca63108fd727d1035173222", 1788084859),
    ("03f6ab5174f50e90bce5645947bf11e6", 1788085018),
]

def make_sign(P, T):
    h1 = hashlib.md5((P + K).encode()).hexdigest()
    h2 = hashlib.md5((P + K + h1 + P).encode()).hexdigest()
    h3 = hashlib.md5((P + K + h1 + P + h2 + T).encode()).hexdigest()
    return hashlib.md5((P + K + h1 + P + h2 + T + h3 + K).encode()).hexdigest()

found = []
for d in range(-32, 33):
    P = chr((ord(path[0]) + d) & 0xFF) + path[1:]
    for off in range(-10, 11):
        hits = sum(1 for sig, ts in fenbi if make_sign(P, str((ts + off) // 60)) == sig)
        if hits:
            print("delta=%d off=%d 命中 %d/5" % (d, off, hits))
            found.append((d, off, hits))
if not found:
    print("delta -32..32 × ts偏移 ±10 全 miss")
    # 附加：T 变体（ts 原样、ts//60*60 等）
    for d in (-1, 0, 1):
        P = chr((ord(path[0]) + d) & 0xFF) + path[1:]
        for name, T in [("ts原值", "1788084659"), ("ts毫秒", "1788084659000")]:
            hits = sum(1 for sig, ts in fenbi if make_sign(P, T) == sig)
            if hits:
                print("delta=%d T=%s 命中 %d/5" % (d, name, hits))
    print("T 变体扫描完成")
