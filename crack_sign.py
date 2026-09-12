import hashlib

# 原版抓包数据（time.delta 都约等于 0，/1000 = 0）
samples = [
    ("/leo-auth/android/user-devices", "7b666b514f2bab92104fdfd08a7e08e8"),
    ("/leo-game-pk/android/math/pk/home", "b4e3e3b0eb3359f66b7d1b32ce42603e"),
    ("/leo-game-pk/android/math/pk/match/v2", "bfd626cda297eaeeb8f2763f0d2b8e72"),
]

KEY = "wdi4n2t8edr"


def md5(s):
    if isinstance(s, str):
        s = s.encode()
    return hashlib.md5(s).hexdigest()


def check(fn, label):
    ok = 0
    for path, want in samples:
        got = fn(path)
        if got == want:
            ok += 1
    if ok > 0:
        print("HIT %s: %d/%d" % (label, ok, len(samples)))


for td in ["0", "1", "-234", "1788520808"]:
    for sep in ["", "-", "_", "&", ":"]:
        check(lambda p, td=td, sep=sep: md5(p + sep + KEY + sep + td), f"path{sep}key{sep}{td}")
        check(lambda p, td=td, sep=sep: md5(KEY + sep + p + sep + td), f"key{sep}path{sep}{td}")
        check(lambda p, td=td, sep=sep: md5(p + sep + td + sep + KEY), f"path{sep}{td}{sep}key")
        check(lambda p, td=td, sep=sep: md5(td + sep + p + sep + KEY), f"{td}{sep}path{sep}key")

print("done")
