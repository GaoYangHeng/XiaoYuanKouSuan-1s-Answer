import hashlib
import itertools

KEY = "wdi4n2t8edr"
PATH = "/leo-game-pk/android/math/pk/match/v2"
V = "TEST_DEVICE_ID_FAKE"
SIGN = "1c2d8ad86accd1deff5023db8927bf3f"

SEPS = ["", "&", "|", "-", "_", "/", ":", ",", "=", "+", " ", "@", "#", "."]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def check(items, sign):
    n = len(items)
    for perm in itertools.permutations(range(n)):
        for sep in SEPS:
            cand = sep.join(items[i] for i in perm)
            if md5(cand) == sign:
                return cand
    return None


def main():
    # ts 分钟 = 29800986，秒 = 1788059161
    for minute in ["29800986", "1788059161", "1788059163"]:
        for sdk in ["34", "36", "14"]:
            for extra in [None, "android", "0", "1"]:
                items = [PATH, KEY, minute, V, sdk]
                if extra is not None:
                    items.append(extra)
                r = check(items, SIGN)
                if r:
                    print("[命中]", repr(r))
                    return
    print("[未命中]")


if __name__ == "__main__":
    main()
