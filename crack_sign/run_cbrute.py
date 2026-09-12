# -*- coding: utf-8 -*-
# 组合爆破：T410(ts) 来自模拟器真实 44280 执行，delta c 爆破
# 假设：真机校验通过 → c=0（模拟器恒 c=-1），T 编码只依赖 ts
import hashlib
import sys
from emulator import Emulator

PATH = "/leo-game-pk/android/math/pk/match/v2"
K = b"wdi4n2t8edr"
K_SIM = "wdi4n2t8edr"
QUERY = ("?pointId=1951&triggerPeakMatch=0&_productId=611&platform=android34"
         "&version=3.141.1&vendor=tencent&av=5&deviceCategory=phone"
         "&webviewVersion=131&whRatio=2.06")

G3 = [  # 组3 Test probe 真机
    (1788059164, "c09aca9582fbe0a788022afbcba3e4af"),
    (1788059228, "95b23547d8c598bc3df4f484620abb49"),
    (1788059354, "a8a69657806a8e639a9c0832225bb405"),
]
G1 = [  # 组1 FENBI 官方真机
    (1788084659, "d9a0ede59cd64436379a3d6e716c3f74"),
    (1788084681, "4d4fb91c395b601b9b61816f16420484"),
    (1788084809, "57e40701ec58b4d9c89f471310ad3270"),
    (1788084859, "296bca5eaca63108fd727d1035173222"),
    (1788085018, "03f6ab5174f50e90bce5645947bf11e6"),
]

class Quiet:
    encoding = "utf-8"
    def __enter__(self):
        self._o = sys.stdout
        sys.stdout = self
        return self
    def __exit__(self, *a):
        sys.stdout = self._o
    def write(self, s):
        return len(s)
    def flush(self):
        pass
    def isatty(self):
        return False

def md5(b):
    return hashlib.md5(b).hexdigest().encode()

def chain(P, T):
    h1 = md5(P + K)
    h2 = md5(P + K + h1 + P)
    h3 = md5(P + K + h1 + P + h2 + T)
    return md5(P + K + h1 + P + h2 + T + h3 + K).decode()

def main():
    hits = 0
    for ts, want in G3 + G1:
        try:
            with Quiet():
                e = Emulator()
                e.time_ret = ts
                e.start(PATH, K_SIM, ts)
                T = getattr(e, "real_T", b"")
        except Exception:
            import traceback
            traceback.print_exc()
            continue
        if not T:
            print(f"ts={ts} 未取得 T410")
            continue
        found = None
        for c in range(-256, 257):
            p0 = chr((ord("/") + c) & 0xFF)
            for base in (PATH, PATH + QUERY, PATH.replace("/", "_", 1)):
                P = (p0 + base[1:]).encode()
                if chain(P, T) == want:
                    found = (c, base[:40])
                    break
            if found:
                break
        if found:
            hits += 1
            print(f"ts={ts} HIT!!! c={found[0]} base={found[1]}")
        else:
            print(f"ts={ts} miss  gotT_len={len(T)}")
        sys.stdout.flush()
    print(f"总计 {hits}/{len(G3)+len(G1)}")

if __name__ == "__main__":
    main()
