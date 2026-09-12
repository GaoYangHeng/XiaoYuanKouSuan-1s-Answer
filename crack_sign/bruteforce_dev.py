import hashlib
import itertools
import datetime

KEY = "wdi4n2t8edr"

# (path, sign, 本地时间)
SAMPLES = [
    ("/leo-game-pk/android/math/pk/match/v2", "7ccaf869bade9bf18c8f0c3e8a034e23", datetime.datetime(2026, 8, 30, 11, 6)),
    ("/leo-game-pk/android/math/pk/match/v2", "cfe580fae28fc66c89610b620c815478", datetime.datetime(2026, 8, 30, 11, 7)),
    ("/leo-game-pk/android/math/pk/match/v2", "8f8118bb867adacf8eecc9c8c139f8b1", datetime.datetime(2026, 8, 30, 11, 13)),
]

DEVICES = [
    "623751490",           # userid
    "350821720",           # ks_deviceid
    "-8977714769984515805",  # YFD_U
    "623751490",
]

SEPS = ["", "&", "|", "-", "_"]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def ts_variants(dt):
    epoch = int(dt.timestamp())
    out = [str(epoch), str(epoch // 60)]
    for f in ["%Y%m%d%H%M", "%Y%m%d%H%M%S", "%Y%m%d", "%Y%m%d%H", "%H%M", "%Y-%m-%d %H:%M"]:
        out.append(dt.strftime(f))
        out.append((dt - datetime.timedelta(hours=8)).strftime(f))
    return list(dict.fromkeys(out))


def solve():
    for path, target, dt in SAMPLES:
        hit = None
        tsvals = ts_variants(dt)
        for t in tsvals:
            for dev in DEVICES:
                items = [path, KEY, t, dev]
                # 常见顺序 + 全排列
                orders = [[0, 1, 2, 3], [0, 2, 1, 3], [3, 0, 1, 2], [0, 1, 3, 2], [0, 3, 1, 2]]
                for order in orders:
                    for sep in SEPS:
                        cand = sep.join(items[i] for i in order)
                        if md5(cand) == target:
                            hit = cand
                            break
                    if hit:
                        break
                if hit:
                    break
            if hit:
                break
        print(f"{'[命中]' if hit else '[未命中]'} {path} {hit!r}")


if __name__ == "__main__":
    solve()
