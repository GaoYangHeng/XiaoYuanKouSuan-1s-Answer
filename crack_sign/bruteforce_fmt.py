import hashlib
import itertools
import datetime

KEY = "wdi4n2t8edr"

# (path, sign, 本地时间 datetime)
SAMPLES = [
    ("/leo-game-pk/android/math/pk/match/v2", "7ccaf869bade9bf18c8f0c3e8a034e23", datetime.datetime(2026, 8, 30, 11, 6)),
    ("/leo-game-pk/android/math/pk/match/v2", "cfe580fae28fc66c89610b620c815478", datetime.datetime(2026, 8, 30, 11, 7)),
    ("/leo-game-pk/android/math/pk/match/v2", "f56ed48991777ba7c272d97167a2619c", datetime.datetime(2026, 8, 30, 11, 9)),
    ("/leo-game-pk/android/math/pk/match/v2", "901574426bac0e001f8ffbf46883b9c0", datetime.datetime(2026, 8, 30, 11, 10)),
    ("/leo-game-pk/android/math/pk/match/v2", "8f8118bb867adacf8eecc9c8c139f8b1", datetime.datetime(2026, 8, 30, 11, 13)),
]

SEPS = ["", "&", "|", "-", "_", "/", "?", ",", ":", "=", "+", " ", "@", "#", "."]

FMT = [
    "%Y%m%d%H%M", "%Y%m%d%H%M%S", "%Y%m%d", "%Y%m%d%H", "%Y%m%d%H%M%S",
    "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%H%M", "%H:%M",
    "%m%d%H%M", "%Y%m%d%H%M", "%d%H%M", "%Y%m%d%H%M",
]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def gen_ts(dt):
    # 本地时间（北京时间 = UTC+8）
    for f in FMT:
        try:
            yield dt.strftime(f)
        except Exception:
            pass
    # UTC 时间
    utc = dt - datetime.timedelta(hours=8)
    for f in FMT:
        try:
            yield utc.strftime(f)
        except Exception:
            pass
    # epoch 秒/分钟（本地时间戳）
    epoch = int(dt.timestamp())
    yield str(epoch)
    yield str(epoch // 60)
    yield str(epoch // 60 * 60)


def solve():
    for path, target, dt in SAMPLES:
        hit = None
        tsvals = list(dict.fromkeys(gen_ts(dt)))
        pv = path
        for t in tsvals:
            items = [pv, KEY, t]
            for perm in itertools.permutations([0, 1, 2]):
                ordered = [items[i] for i in perm]
                for sep in SEPS:
                    cand = sep.join(ordered)
                    if md5(cand) == target:
                        hit = cand
                        break
                if hit:
                    break
            if hit:
                break
        if hit:
            print(f"[命中] {path} -> {hit!r}")
        else:
            print(f"[未命中] {path}")


if __name__ == "__main__":
    solve()
