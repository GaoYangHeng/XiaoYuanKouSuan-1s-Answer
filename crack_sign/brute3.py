import hashlib
import itertools

KEY = "wdi4n2t8edr"
PATH = "/leo-game-pk/android/math/pk/match/v2"
AID = "39c0141952095d9c"
DEVID = "350821720"

# (Unix秒, sign) 样本
SAMPLES = [
    (1788059164, "7ccaf869bade9bf18c8f0c3e8a034e23"),
    (1788059228, "cfe580fae28fc66c89610b620c815478"),
    (1788059354, "f56ed48991777ba7c272d97167a2619c"),
    (1788059447, "901574426bac0e001f8ffbf46883b9c0"),
    (1788059616, "8f8118bb867adacf8eecc9c8c139f8b1"),
]

SEPS = ["", "&", "|", "-", "_", "/", ":", ",", "=", "+", " ", "@", "#", ".", "~"]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def ts_variants(sec):
    m = sec // 60
    return {
        "minute": str(m),
        "seconds": str(sec),
        "floored": str(sec - sec % 60),
        "minute_x60": str(m * 60),
    }


def build_candidates(pools):
    # pools: list of lists of components；对每组，枚举所有排列 × 分隔符
    for pool in pools:
        n = len(pool)
        for perm in itertools.permutations(range(n)):
            for sep in SEPS:
                yield sep.join(pool[i] for i in perm)


def main():
    # 每个样本都要命中才算找到
    targets = {s[1] for s in SAMPLES}

    for tname, tv in ts_variants(SAMPLES[0][0]).items():
        # 不同样本的 timestamp 不同，先按样本0的时间格式推导，再逐样本验证
        pools = [
            [PATH, KEY, tv, AID],
            [PATH, KEY, AID, tv],
            [PATH, tv, KEY, AID],
            [KEY, PATH, tv, AID],
            [AID, PATH, KEY, tv],
            [PATH, KEY, tv, DEVID],
            [PATH, KEY, DEVID, tv],
        ]
        seen = set()
        for cand in build_candidates(pools):
            if cand in seen:
                continue
            seen.add(cand)
            # 验证全部样本
            ok = True
            for sec, sign in SAMPLES:
                tvs = ts_variants(sec)[tname]
                # 用该样本的 timestamp 替换 tv
                cc = cand.replace(tv, tvs, 1)
                if md5(cc) != sign:
                    ok = False
                    break
            if ok:
                print(f"[命中] 时间格式={tname} -> {cand!r}")
                return
        print(f"[未命中] 时间格式 {tname}")
    print("全部未命中")


if __name__ == "__main__":
    main()
