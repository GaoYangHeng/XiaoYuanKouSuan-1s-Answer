import hashlib
import itertools
import struct

samples = [
    ("/leo-auth/android/user-devices", "7b666b514f2bab92104fdfd08a7e08e8"),
    ("/leo-game-pk/android/math/pk/home", "b4e3e3b0eb3359f66b7d1b32ce42603e"),
    ("/leo-game-pk/android/math/pk/match/v2", "bfd626cda297eaeeb8f2763f0d2b8e72"),
]

KEY = "wdi4n2t8edr"
CERT_SHA256 = "70d001ff8eb69642213465d82add355d5b9400f84050f63d34ffa2f69797b42e"
CERT_SHA1 = "e1d63c378b5da5f8d72fe99088be008b6b9644fe"
CERT_MD5 = "0eccddb9491269bf92a7ca9988f91ab3"

def md5(b):
    if isinstance(b, str):
        b = b.encode()
    return hashlib.md5(b).hexdigest()

# 元素定义：每个元素有多个"表示"
# path 用 lambda（依赖样本），其他用字符串
time_reps = ["0", "00", "000"]
sdk_reps = ["34", "034"]
cert_reps = [CERT_SHA256, CERT_SHA1, CERT_MD5, CERT_SHA256.upper(), CERT_SHA1.upper(), CERT_MD5.upper()]

# 也测试字节级：int32 little-endian
def int32_le(v):
    return struct.pack("<i", v).hex()

hits = []

# 字符串拼接测试（5 元素排列）
seps = ["", "-", "_", "&", ":"]
for order in itertools.permutations(range(5)):  # 0=path,1=key,2=time,3=sdk,4=cert
    for sep in seps:
        for tr in time_reps:
            for sr in sdk_reps:
                for cr in cert_reps:
                    def mk(p, order=order, sep=sep, tr=tr, sr=sr, cr=cr):
                        vals = []
                        for o in order:
                            if o == 0: vals.append(p)
                            elif o == 1: vals.append(KEY)
                            elif o == 2: vals.append(tr)
                            elif o == 3: vals.append(sr)
                            else: vals.append(cr)
                        return md5(sep.join(vals))
                    ok = sum(1 for p, w in samples if mk(p) == w)
                    if ok >= 3:
                        hits.append(("str", order, sep, tr, sr, cr))
                        print("HIT str order=%s sep=%r time=%s sdk=%s cert=%s" % (order, sep, tr, sr, cr[:12]))

# 字节级拼接（path_utf8 + key + int32(time) + int32(sdk) + cert_hex_utf8）
for order in itertools.permutations(range(5)):
    for tr in time_reps:
        for sr in sdk_reps:
            for cr in cert_reps:
                def mk_bytes(p, order=order, tr=tr, sr=sr, cr=cr):
                    parts = [p.encode(), KEY.encode(), tr.encode(), sr.encode(), cr.encode()]
                    return md5(b"".join(parts[o] for o in order))
                ok = sum(1 for p, w in samples if mk_bytes(p) == w)
                if ok >= 3:
                    hits.append(("bytes", order, "", tr, sr, cr))
                    print("HIT bytes order=%s time=%s sdk=%s cert=%s" % (order, tr, sr, cr[:12]))

print("\n=== total hits ===", len(hits))
