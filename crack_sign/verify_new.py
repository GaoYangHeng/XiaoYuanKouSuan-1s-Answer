import hashlib

path = "/leo-game-pk/android/math/pk/match/v2"
key = "wdi4n2t8edr"

samples = [
    (1788059164, "c09aca9582fbe0a788022afbcba3e4af"),
    (1788059228, "95b23547d8c598bc3df4f484620abb49"),
    (1788059354, "a8a69657806a8e639a9c0832225bb405"),
    (1788059447, "70c639287005f7c5b91e0719eac597bd"),
    (1788059616, "4ce209b0302810cd6c85b97fc42e1e8b"),
]

def md5(s):
    if isinstance(s, str):
        s = s.encode()
    return hashlib.md5(s).hexdigest()

def make_sign(p, k, ts, d):
    pm = chr((ord(p[0]) + d) & 0xFF) + p[1:]
    minute = str(ts // 60)
    s = pm + k
    h1 = md5(s)
    s = pm + k + h1 + pm
    h2 = md5(s)
    s = pm + k + h1 + pm + h2 + minute
    h3 = md5(s)
    s = pm + k + h1 + pm + h2 + minute + h3 + k
    return md5(s)

# 扫描 delta
for d in range(-5, 6):
    ok = sum(1 for ts, sig in samples if make_sign(path, key, ts, d) == sig)
    if ok > 0:
        print("delta=%d 命中 %d/%d" % (d, ok, len(samples)))
        for ts, sig in samples:
            calc = make_sign(path, key, ts, d)
            print("  ts=%d %s %s" % (ts, calc, "OK" if calc == sig else "X"))
    else:
        print("delta=%d 命中 0" % d)
