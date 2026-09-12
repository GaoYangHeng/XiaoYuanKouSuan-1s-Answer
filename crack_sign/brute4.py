import hashlib
import itertools

KEY = "wdi4n2t8edr"
PATH = "/leo-game-pk/android/math/pk/match/v2"

# 设备 ID 候选（来自抓包 + 之前会话）
DEVICES = [
    "39c0141952095d9c",          # 疑似 Android ID
    "350821720",                 # ks_deviceid
    "-8977714769984515805",      # YFD_U
    "DUcQeOjU71a2CBsqifH5VYmGHNyI2E4i8tg2",  # 数盟 did
    "623751490",                 # userid
]

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


def build_combos(components):
    n = len(components)
    seen = set()
    for perm in itertools.permutations(range(n)):
        for sep in SEPS:
            s = sep.join(components[i] for i in perm)
            if s not in seen:
                seen.add(s)
                yield s


def main():
    # 1) 纯拼接 path/key/ts/device（含空 device）
    for dev in DEVICES + [""]:
        for tname in ts_variants(SAMPLES[0][0]):
            tv0 = ts_variants(SAMPLES[0][0])[tname]
            pools = [
                [PATH, KEY, tv0, dev],
                [PATH, KEY, dev, tv0],
                [KEY, PATH, tv0, dev],
                [dev, PATH, KEY, tv0],
            ]
            for pool in pools:
                for cand in build_combos(pool):
                    ok = True
                    for sec, sign in SAMPLES:
                        tv = ts_variants(sec)[tname]
                        cc = cand.replace(tv0, tv, 1)
                        if md5(cc) != sign:
                            ok = False
                            break
                    if ok:
                        print(f"[命中-拼接] dev={dev!r} t={tname} -> {cand!r}")
                        return

    # 2) 嵌套 MD5：MD5(内层) 再与外层组合
    for dev in DEVICES + [""]:
        for tname in ts_variants(SAMPLES[0][0]):
            tv0 = ts_variants(SAMPLES[0][0])[tname]
            # 内层候选
            inner_pools = [
                [PATH, KEY], [PATH, dev], [KEY, dev], [PATH, KEY, dev],
                [PATH, tv0], [KEY, tv0], [dev, tv0], [PATH, KEY, tv0],
            ]
            for inner_pool in inner_pools:
                for inner in build_combos(inner_pool):
                    h = md5(inner)
                    # 外层组合
                    outer_pools = [
                        [h, dev, tv0], [h, tv0, dev], [PATH, h, tv0],
                        [h, PATH, tv0], [h, dev], [h, tv0],
                    ]
                    for outer_pool in outer_pools:
                        for cand in build_combos(outer_pool):
                            ok = True
                            for sec, sign in SAMPLES:
                                tv = ts_variants(sec)[tname]
                                hh = md5(inner.replace(tv0, tv, 1))
                                cc = cand.replace(tv0, tv, 1).replace(h, hh, 1)
                                if md5(cc) != sign:
                                    ok = False
                                    break
                            if ok:
                                print(f"[命中-嵌套] dev={dev!r} t={tname} inner={inner!r} outer={cand!r}")
                                return

    print("全部未命中")


if __name__ == "__main__":
    main()
