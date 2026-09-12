import hashlib
import itertools
import datetime

KEY = "wdi4n2t8edr"

SAMPLES = [
    ("/leo-game-pk/android/math/pk/match/v2", "7ccaf869bade9bf18c8f0c3e8a034e23", datetime.datetime(2026, 8, 30, 11, 6)),
    ("/leo-game-pk/android/math/pk/match/v2", "cfe580fae28fc66c89610b620c815478", datetime.datetime(2026, 8, 30, 11, 7)),
    ("/leo-game-pk/android/math/pk/multi/match/v2", "82ef6c3753a9582be8186b562771cf44", datetime.datetime(2026, 8, 30, 11, 7)),
    ("/leo-game-pk/android/math/pk/match/v2", "f56ed48991777ba7c272d97167a2619c", datetime.datetime(2026, 8, 30, 11, 9)),
    ("/leo-game-pk/android/word/eliminate/match/v2", "4364c6b8e228c3e3318da07c663ee724", datetime.datetime(2026, 8, 30, 11, 10)),
    ("/leo-game-pk/android/math/pk/match/v2", "901574426bac0e001f8ffbf46883b9c0", datetime.datetime(2026, 8, 30, 11, 10)),
    ("/leo-game-pk/android/math/pk/match/v2", "8f8118bb867adacf8eecc9c8c139f8b1", datetime.datetime(2026, 8, 30, 11, 13)),
]

DEVICES = [
    "0123456789abcdef",       # android_id
    "A2NMVB1816014342",       # serialno
    "623751490",              # userid
    "350821720",              # ks_deviceid
    "-8977714769984515805",   # YFD_U
]

SEPS = ["", "&", "|", "-", "_", "/", ":", ","]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def ts_variants(dt):
    epoch = int(dt.timestamp())
    out = [str(epoch), str(epoch // 60), str(epoch // 60 * 60)]
    for f in ["%Y%m%d%H%M", "%Y%m%d%H%M%S", "%Y%m%d", "%Y%m%d%H", "%H%M",
              "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m%d%H%M"]:
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
                for perm in itertools.permutations([0, 1, 2, 3]):
                    for sep in SEPS:
                        cand = sep.join(items[i] for i in perm)
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
