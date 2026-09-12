# -*- coding: utf-8 -*-
# patched .so 离线验证：delta≡0 后 Unicorn 直出应命中组1官方真机 + solar
# 对照：Python 链公式（P原样 + e.real_T）
import hashlib
import sys
import emulator

emulator.SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\libRequestEncoder_patched.so"
from emulator import Emulator

PATH = "/leo-game-pk/android/math/pk/match/v2"
SOLAR = "/solar-activity/android/activity/6"
K = "wdi4n2t8edr"
KB = b"wdi4n2t8edr"

GOLDS = [
    (PATH, 1788084659, "d9a0ede59cd64436379a3d6e716c3f74", "组1-FENBI"),
    (PATH, 1788084681, "4d4fb91c395b601b9b61816f16420484", "组1-FENBI"),
    (PATH, 1788084809, "57e40701ec58b4d9c89f471310ad3270", "组1-FENBI"),
    (PATH, 1788084859, "296bca5eaca63108fd727d1035173222", "组1-FENBI"),
    (PATH, 1788085018, "03f6ab5174f50e90bce5645947bf11e6", "组1-FENBI"),
    (SOLAR, 1788084650, "68637e3ae7506ac7c0328b7a146882dc", "solar对照"),
    (PATH, 1788059164, "c09aca9582fbe0a788022afbcba3e4af", "组3-Test"),
    (PATH, 1788059228, "95b23547d8c598bc3df4f484620abb49", "组3-Test"),
    (PATH, 1788059354, "a8a69657806a8e639a9c0832225bb405", "组3-Test"),
]


def md5(b):
    return hashlib.md5(b).hexdigest().encode()


def chain(P, T):
    h1 = md5(P + KB)
    h2 = md5(P + KB + h1 + P)
    h3 = md5(P + KB + h1 + P + h2 + T)
    return md5(P + KB + h1 + P + h2 + T + h3 + KB).decode()


def main():
    hits = 0
    for path, ts, want, grp in GOLDS:
        try:
            e = Emulator()
            e.time_ret = ts
            e.start(path, K, ts)
            got = e.final_sign
            T = getattr(e, "real_T", b"")
            py = chain(path.encode(), T) if T else "?"
            tag = "HIT!!!" if got == want else "miss"
            if got == want:
                hits += 1
            agree = "双路一致" if py == got else f"双路不一致 py={py}"
            print(f"[{grp}] ts={ts} -> {tag} {agree}")
        except Exception as ex:
            import traceback
            traceback.print_exc()
            print(f"[{grp}] ts={ts} 异常: {type(ex).__name__}: {ex}")
        sys.stdout.flush()
    print(f"\nUnicorn 直出命中 {hits}/{len(GOLDS)}")
    print("预期：组1(5)+solar(1) 应全 HIT；组3 3 个 miss 属预期（Test 污染值）")


if __name__ == "__main__":
    main()
