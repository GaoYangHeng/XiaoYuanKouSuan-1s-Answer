import hashlib
import itertools

KEY = "wdi4n2t8edr"
PATH = "/leo-game-pk/android/math/pk/match/v2"
SALT = "javamPMLan"

DEVICES = ["39c0141952095d9c", "350821720", "", "DUcQeOjU71a2CBsqifH5VYmGHNyI2E4i8tg2", "623751490"]

SAMPLES = [
    (1788059164, "7ccaf869bade9bf18c8f0c3e8a034e23"),
    (1788059228, "cfe580fae28fc66c89610b620c815478"),
    (1788059354, "f56ed48991777ba7c272d97167a2619c"),
    (1788059447, "901574426bac0e001f8ffbf46883b9c0"),
    (1788059616, "8f8118bb867adacf8eecc9c8c139f8b1"),
]

SEPS = ["", "&", "|", "-", "_", "/", ":", ",", "=", "+", "@", "#", "."]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def combos(components):
    n = len(components)
    for perm in itertools.permutations(range(n)):
        for sep in SEPS:
            yield sep.join(components[i] for i in perm)


for dev in DEVICES:
    for t in [str(SAMPLES[0][0] // 60), str(SAMPLES[0][0]), str(SAMPLES[0][0] - SAMPLES[0][0] % 60)]:
        pools = [
            [PATH, KEY, t, dev, SALT],
            [PATH, KEY, t, SALT],
            [KEY, PATH, t, dev, SALT],
        ]
        for pool in pools:
            for cand in combos(pool):
                ok = True
                for sec, sign in SAMPLES:
                    tv = str(sec // 60) if len(t) == 8 else (str(sec) if len(t) == 10 else str(sec - sec % 60))
                    cc = cand.replace(t, tv, 1)
                    if md5(cc) != sign:
                        ok = False
                        break
                if ok:
                    print(f"[命中] dev={dev!r} t={t!r} -> {cand!r}")
                    raise SystemExit
print("未命中")
