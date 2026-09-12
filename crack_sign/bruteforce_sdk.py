import hashlib
import itertools
import datetime

KEY = "wdi4n2t8edr"
AID = "39c0141952095d9c"
SDK = "34"

SAMPLES = [
    ("/leo-game-pk/android/math/pk/match/v2", "7ccaf869bade9bf18c8f0c3e8a034e23", datetime.datetime(2026, 8, 30, 11, 6)),
    ("/leo-game-pk/android/math/pk/match/v2", "cfe580fae28fc66c89610b620c815478", datetime.datetime(2026, 8, 30, 11, 7)),
    ("/leo-game-pk/android/math/pk/match/v2", "8f8118bb867adacf8eecc9c8c139f8b1", datetime.datetime(2026, 8, 30, 11, 13)),
]

SEPS = ["", "&", "|", "-", "_", "/", ":", ",", "=", "+", " ", "@", "#", "."]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def ts_variants(dt):
    epoch = int(dt.timestamp())
    out = [str(epoch), str(epoch // 60), str(epoch // 60 * 60), str(epoch * 1000)]
    for f in ["%Y%m%d%H%M", "%Y%m%d%H%M%S", "%Y%m%d", "%Y%m%d%H", "%H%M", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
        out.append(dt.strftime(f))
        out.append((dt - datetime.timedelta(hours=8)).strftime(f))
    return list(dict.fromkeys(out))


def solve():
    for path, target, dt in SAMPLES:
        hit = None
        tsvals = ts_variants(dt)
        for t in tsvals:
            # 元素组合：path, key, ts, android_id, sdk（选 3-5 个元素）
            pools = [
                [path, KEY, t],
                [path, KEY, t, AID],
                [path, KEY, t, AID, SDK],
                [path, KEY, t, SDK],
                [path, AID, t],
            ]
            for items in pools:
                n = len(items)
                for perm in itertools.permutations(range(n)):
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
