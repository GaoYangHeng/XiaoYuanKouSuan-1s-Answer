import hashlib
import itertools

KEY = "wdi4n2t8edr"
PATH = "/leo-game-pk/android/math/pk/match/v2"

# 2026-08-30 抓包样本：(Unix秒, sign)
SAMPLES = [
    (1788059164, "7ccaf869bade9bf18c8f0c3e8a034e23"),  # 11:06:03
    (1788059228, "cfe580fae28fc66c89610b620c815478"),  # 11:07:07
    (1788059354, "f56ed48991777ba7c272d97167a2619c"),  # 11:09:13
    (1788059447, "901574426bac0e001f8ffbf46883b9c0"),  # 11:10:46
    (1788059616, "8f8118bb867adacf8eecc9c8c139f8b1"),  # 11:13:35
]

SEPS = ["", "&", "|", "-", "_", "/", ":", ",", "=", "+", " ", "@", "#", ".", "~"]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def ts_variants(sec):
    m = sec // 60
    return [str(m), str(sec), str(sec - (sec % 60)), str(sec * 1000)]


def main():
    for sec, target in SAMPLES:
        tvars = ts_variants(sec)
        found = False
        for t in tvars:
            pools = [
                [PATH, KEY, t],
                [KEY, PATH, t],
                [PATH, t, KEY],
                [KEY, t, PATH],
                [t, PATH, KEY],
                [t, KEY, PATH],
            ]
            for items in pools:
                n = len(items)
                for perm in itertools.permutations(range(n)):
                    for sep in SEPS:
                        cand = sep.join(items[i] for i in perm)
                        if md5(cand) == target:
                            print(f"[命中] sec={sec} t={t} -> {cand!r}")
                            found = True
        if not found:
            print(f"[未命中] sec={sec} sign={target}")
    print("完成")


if __name__ == "__main__":
    main()
