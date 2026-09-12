import hashlib
import itertools

KEY = "wdi4n2t8edr"

# (path, sign, ref_sec)
SAMPLES = [
    ("/leo-game-pk/android/math/pk/match/v2", "7ccaf869bade9bf18c8f0c3e8a034e23", 1788059163),
    ("/leo-game-pk/android/math/pk/match/v2", "cfe580fae28fc66c89610b620c815478", 1788059227),
    ("/leo-game-pk/android/math/pk/multi/match/v2", "82ef6c3753a9582be8186b562771cf44", 1788059239),
    ("/leo-game-pk/android/math/pk/match/v2", "f56ed48991777ba7c272d97167a2619c", 1788059353),
    ("/leo-game-pk/android/word/eliminate/match/v2", "4364c6b8e228c3e3318da07c663ee724", 1788059227),
    ("/leo-game-pk/android/math/pk/match/v2", "901574426bac0e001f8ffbf46883b9c0", 1788059446),
    ("/leo-game-pk/android/math/pk/match/v2", "8f8118bb867adacf8eecc9c8c139f8b1", 1788059615),
]

SEPS = ["", "&", "|", "-", "_", "/", "?", ",", ":", "=", "+", " ", "@", "#", "."]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def path_variants(p):
    yield p
    yield p.lstrip("/")
    yield "https://xyks.yuanfudao.com" + p
    yield "xyks.yuanfudao.com" + p


def ts_variants(sec):
    m = sec // 60
    yield str(sec)
    yield str(m)
    yield hex(sec)[2:]
    yield hex(m)[2:]
    yield str(sec * 1000)
    yield str(sec // 600)


def solve():
    for path, target, ref in SAMPLES:
        hit = None
        for pv in path_variants(path):
            for delta in range(-120, 121):
                sec = ref + delta
                for t in ts_variants(sec):
                    items = [pv, KEY, t]
                    for perm in itertools.permutations([0, 1, 2]):
                        ordered = [items[i] for i in perm]
                        for sep in SEPS:
                            cand = sep.join(ordered)
                            if md5(cand) == target:
                                hit = (pv, cand)
                                break
                        if hit:
                            break
                    if hit:
                        break
                if hit:
                    break
            if hit:
                break
        if hit:
            print(f"[命中] {path} -> {hit[1]!r}")
        else:
            print(f"[未命中] {path}")


if __name__ == "__main__":
    solve()
