import hashlib
import itertools
from datetime import datetime, timezone, timedelta

KEY = "wdi4n2t8edr"
PATH = "/leo-game-pk/android/math/pk/match/v2"

DEVICES = [
    "39c0141952095d9c",
    "350821720",
    "-8977714769984515805",
    "DUcQeOjU71a2CBsqifH5VYmGHNyI2E4i8tg2",
    "623751490",
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
    out = {
        "minute": str(m),
        "seconds": str(sec),
        "floored": str(sec - sec % 60),
    }
    # 时区尝试：UTC 和 UTC+8 (CST)
    for tzname, tz in [("utc", timezone.utc), ("cst", timezone(timedelta(hours=8)))]:
        for fmt in ["%Y%m%d%H%M", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M",
                    "%Y%m%d%H", "%H%M", "%Y%m%d", "%m%d%H%M", "%d%H%M"]:
            dt = datetime.fromtimestamp(sec, tz)
            out[f"{tzname}_{fmt}"] = dt.strftime(fmt)
    return out


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
    tvnames = list(ts_variants(SAMPLES[0][0]).keys())
    for dev in DEVICES + [""]:
        for tname in tvnames:
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
                        print(f"[命中] dev={dev!r} t={tname} -> {cand!r}")
                        return
    print("全部未命中")


if __name__ == "__main__":
    main()
