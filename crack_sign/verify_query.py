# -*- coding: utf-8 -*-
# 判别：sign 输入是纯 path 还是 path+query
import hashlib

K = "wdi4n2t8edr"
path = "/leo-game-pk/android/math/pk/match/v2"
query = "pointId=1951&triggerPeakMatch=0&_productId=611&platform=android34&version=3.141.1&vendor=tencent&av=5&deviceCategory=phone&webviewVersion=131&whRatio=2.06"

fenbi = [
    ("d9a0ede59cd64436379a3d6e716c3f74", 1788084659),
    ("4d4fb91c395b601b9b61816f16420484", 1788084681),
    ("57e40701ec58b4d9c89f471310ad3270", 1788084809),
    ("296bca5eaca63108fd727d1035173222", 1788084859),
    ("03f6ab5174f50e90bce5645947bf11e6", 1788085018),
]

def md5s(s):
    return hashlib.md5s(s.encode()) if hasattr(hashlib, "md5s") else hashlib.md5(s.encode()).hexdigest()

def make_sign(P, ts):
    T = str(ts // 60)
    h1 = hashlib.md5((P + K).encode()).hexdigest()
    h2 = hashlib.md5((P + K + h1 + P).encode()).hexdigest()
    h3 = hashlib.md5((P + K + h1 + P + h2 + T).encode()).hexdigest()
    return hashlib.md5((P + K + h1 + P + h2 + T + h3 + K).encode()).hexdigest()

# P 变体池
variants = {
    "纯path首-1": chr(ord(path[0]) - 1) + path[1:],
    "path?query首-1": chr(ord(path[0]) - 1) + path[1:] + "?" + query,
    "path+query首-1": chr(ord(path[0]) - 1) + path[1:] + query,
    "pq首-1无问号": chr(ord(path[0]) - 1) + (path + "?" + query)[1:],
    "纯path原样": path,
    "path?query原样": path + "?" + query,
}

for name, P in variants.items():
    ok = sum(1 for sig, ts in fenbi if make_sign(P, ts) == sig)
    print("%-16s 命中 %d/5" % (name, ok))
    if ok:
        for sig, ts in fenbi:
            for off in range(-90, 91):
                if make_sign(P, ts + off) == sig:
                    print("   %s ts偏移=%d HIT" % (sig[:8], off))
                    break
