# -*- coding: utf-8 -*-
# 矩阵实验：强制 memcmp 结果（0=校验通过 / 1=失败）× 组3 真机样本
# 假设：模拟环境 memcmp#1 不等 → 走异常分支；真机相等 → 正常分支
import sys
from emulator import Emulator

PATH = "/leo-game-pk/android/math/pk/match/v2"
K = "wdi4n2t8edr"
# 组3 Test 签名 probe 真机样本
GOLDS = [
    (1788059164, "c09aca9582fbe0a788022afbcba3e4af"),
    (1788059228, "95b23547d8c598bc3df4f484620abb49"),
    (1788059354, "a8a69657806a8e639a9c0832225bb405"),
]

class Quiet:
    """吞掉 emulator 内部 print，避免刷屏"""
    def __enter__(self):
        self._o = sys.stdout
        sys.stdout = self
        return self
    def __exit__(self, *a):
        sys.stdout = self._o
    def write(self, s):
        pass
    def flush(self):
        pass

def main():
    hits = 0
    for force in (0, 1):
        for ts, want in GOLDS:
            try:
                with Quiet():
                    e = Emulator()
                    e.time_ret = ts
                    e.memcmp_force = force
                    e.start(PATH, K, ts)
                    got = e.final_sign
            except Exception as ex:
                got = f"ERR:{type(ex).__name__}"
            ok = "HIT!!!" if got == want else "miss"
            if got == want:
                hits += 1
            print(f"force={force} ts={ts} got={got} want={want} -> {ok}")
            sys.stdout.flush()
    print(f"总计 {hits}/6")

if __name__ == "__main__":
    main()
