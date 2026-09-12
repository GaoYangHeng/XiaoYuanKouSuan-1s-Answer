import hashlib
import itertools

KEY = "wdi4n2t8edr"
PATH = "/leo-game-pk/android/math/pk/match/v2"
AID = "39c0141952095d9c"
SHA256 = "cae28ac067e030162deac0a65394717a6d89066d906f80631eb800ae3d16c8bf"
SHA1 = "e0a12e7aae5d1f7905f0783d3910fff872a46e8d"
SIGN = "cfba652c67886d4ca1a197cfb9bef8d0"

SEPS = ["", "&", "|", "-", "_", "/", ":", ",", "=", "+", " ", "@", "#", "."]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def check(items):
    n = len(items)
    for perm in itertools.permutations(range(n)):
        for sep in SEPS:
            cand = sep.join(items[i] for i in perm)
            if md5(cand) == SIGN:
                return cand
    return None


def main():
    tss = ["29800986", "1788059161", "1788059163"]
    for t in tss:
        pools = [
            [PATH, KEY, t, AID, SHA256],
            [PATH, KEY, t, AID, SHA1],
            [PATH, KEY, t, SHA256],
            [PATH, KEY, t, AID],
            [PATH, KEY, t, AID, SHA256, "34"],
            [PATH, KEY, t, AID, SHA1, "34"],
        ]
        for items in pools:
            r = check(items)
            if r:
                print("[命中]", repr(r))
                return
    print("[未命中]")


if __name__ == "__main__":
    main()
