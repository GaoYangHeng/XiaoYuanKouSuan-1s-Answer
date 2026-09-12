import hashlib
import itertools

KEY = "wdi4n2t8edr"
PATH = "/leo-game-pk/android/math/pk/match/v2"
MINUTE = "29800986"        # 1788059161 // 60
V = "TEST_DEVICE_ID_FAKE"  # SecureStub.getString 返回值
SIGN = "1c2d8ad86accd1deff5023db8927bf3f"  # ts=1788059161 的输出

SEPS = ["", "&", "|", "-", "_", "/", ":", ",", "=", "+", " ", "@", "#", "."]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def main():
    items = [PATH, KEY, MINUTE, V]
    for perm in itertools.permutations(range(4)):
        for sep in SEPS:
            cand = sep.join(items[i] for i in perm)
            if md5(cand) == SIGN:
                print("[命中]", repr(cand))
                return
    # 也试试 ts 用秒、用其他格式
    for t in ["1788059161", "1788059161000", "202608301106", "1106", "2026-08-30 11:06"]:
        items = [PATH, KEY, t, V]
        for perm in itertools.permutations(range(4)):
            for sep in SEPS:
                cand = sep.join(items[i] for i in perm)
                if md5(cand) == SIGN:
                    print("[命中]", repr(cand))
                    return
    print("[未命中]")


if __name__ == "__main__":
    main()
