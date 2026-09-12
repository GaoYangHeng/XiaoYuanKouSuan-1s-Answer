import hashlib

samples = [
    ("/leo-auth/android/user-devices", "7b666b514f2bab92104fdfd08a7e08e8"),
    ("/leo-game-pk/android/math/pk/home", "b4e3e3b0eb3359f66b7d1b32ce42603e"),
    ("/leo-game-pk/android/math/pk/match/v2", "bfd626cda297eaeeb8f2763f0d2b8e72"),
]

KEY = "wdi4n2t8edr"
CERT_SHA256 = "70d001ff8eb69642213465d82add355d5b9400f84050f63d34ffa2f69797b42e"
CERT_SHA1 = "e1d63c378b5da5f8d72fe99088be008b6b9644fe"
CERT_MD5 = "0eccddb9491269bf92a7ca9988f91ab3"

TIME = "0"

hits = []


def md5(s):
    if isinstance(s, str):
        s = s.encode()
    return hashlib.md5(s).hexdigest()


def try_combo(label, func):
    ok = 0
    for p, w in samples:
        if func(p) == w:
            ok += 1
    if ok > 0:
        hits.append((ok, label))
        print("HIT %d/%d: %s" % (ok, len(samples), label))


for cert_name, cert_hash in [("sha256", CERT_SHA256), ("sha1", CERT_SHA1), ("md5", CERT_MD5)]:
    for sep in ["", "-", "_", "&"]:
        # 4 元素排列
        for td in [TIME, "1788520808", "-234"]:
            parts = [lambda p: p, KEY, cert_hash, td]
            # 所有排列
            for i in range(4):
                for j in range(4):
                    if j == i:
                        continue
                    for k in range(4):
                        if k == i or k == j:
                            continue
                        for l in range(4):
                            if l == i or l == j or l == k:
                                continue
                            order = [i, j, k, l]

                            def mk(p, order=order, sep=sep, parts=parts, td=td):
                                vals = [parts[o] if isinstance(parts[o], str) else parts[o](p) for o in order]
                                return md5(sep.join(vals))

                            try_combo("cert=%s td=%s sep=%r order=%s" % (cert_name, td, sep, order), mk)

print("\n=== summary ===")
for ok, label in sorted(hits, reverse=True):
    print("%d/%d: %s" % (ok, len(samples), label))