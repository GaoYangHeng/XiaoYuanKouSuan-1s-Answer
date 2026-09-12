# -*- coding: utf-8 -*-
# 决定性实验：用 Unicorn（真实 T，.so 44280 原生执行）对全部黄金样本逐个复算
# 样本权威来源：verify_golds.py
import sys
from emulator import Emulator

PATH = "/leo-game-pk/android/math/pk/match/v2"
SOLAR = "/solar-activity/android/activity/6"
K = "wdi4n2t8edr"

# (path, ts, 期望sign, 组别)
GOLDS = [
    (PATH, 1788059164, "c09aca9582fbe0a788022afbcba3e4af", "组3-Test"),
    (PATH, 1788059228, "95b23547d8c598bc3df4f484620abb49", "组3-Test"),
    (PATH, 1788059354, "a8a69657806a8e639a9c0832225bb405", "组3-Test"),
    (PATH, 1788059615, "e0302beeadb745ecbbfeb2e8f86d426d", "组2-AVD"),
    (PATH, 1788084659, "d9a0ede59cd64436379a3d6e716c3f74", "组1-FENBI"),
    (PATH, 1788084681, "4d4fb91c395b601b9b61816f16420484", "组1-FENBI"),
    (PATH, 1788084809, "57e40701ec58b4d9c89f471310ad3270", "组1-FENBI"),
    (PATH, 1788084859, "296bca5eaca63108fd727d1035173222", "组1-FENBI"),
    (PATH, 1788085018, "03f6ab5174f50e90bce5645947bf11e6", "组1-FENBI"),
    (SOLAR, 1788084650, "68637e3ae7506ac7c0328b7a146882dc", "solar对照"),
]

def main():
    hits = 0
    for path, ts, want, grp in GOLDS:
        try:
            e = Emulator()
            e.time_ret = ts
            e.start(path, K, ts)
            got = e.final_sign
            outs = getattr(e, "_vsnp_outs", [])
            tseg = outs[2].decode("ascii", "replace") if len(outs) > 2 else ""
            ok = "HIT!!!" if got == want else "miss"
            if got == want:
                hits += 1
            print(f"[{grp}] ts={ts} T_len={len(tseg)}")
            print(f"    got={got}")
            print(f"    want={want}  -> {ok}")
            if got != want and tseg:
                print(f"    T段前80={tseg[:80]}")
        except Exception as ex:
            print(f"[{grp}] ts={ts} 异常: {type(ex).__name__}: {ex}")
        sys.stdout.flush()
    print(f"\n总计 {hits}/{len(GOLDS)} 命中")

if __name__ == "__main__":
    main()
