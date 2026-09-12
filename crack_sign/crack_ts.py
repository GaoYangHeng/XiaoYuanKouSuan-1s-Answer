import hashlib
import itertools

path = "/leo-game-pk/android/math/pk/match/v2"
key = "wdi4n2t8edr"

samples = [
    (1788059164, "c09aca9582fbe0a788022afbcba3e4af"),
    (1788059228, "95b23547d8c598bc3df4f484620abb49"),
    (1788059354, "a8a69657806a8e639a9c0832225bb405"),
]

def md5(s):
    if isinstance(s, str):
        s = s.encode()
    return hashlib.md5(s).hexdigest()

# Test 签名哈希 + android_id
CERT_SHA256 = "cae28ac067e030162deac0a65394717a6d89066d906f80631eb800ae3d16c8bf"
CERT_MD5 = "da8e2ec9722dee7ab20752a92e588667"
AID = "39c0141952095d9c"
SDK = "34"

# 签名可能的形式
cert_forms = [CERT_SHA256, CERT_MD5, CERT_SHA256.upper(), CERT_MD5.upper(),
              md5(CERT_SHA256), md5(CERT_MD5)]

def check_all(func, label):
    ok = sum(1 for ts, sig in samples if func(ts) == sig)
    if ok > 0:
        print("HIT %d/%d: %s" % (ok, len(samples), label))
        return True
    return False

# 基础 make_sign（4 轮），签名插入到各拼接点
def make_base(ts, extra, d=-1):
    pm = chr((ord(path[0]) + d) & 0xFF) + path[1:]
    minute = str(ts // 60)
    s = pm + key + extra
    h1 = md5(s)
    s = pm + key + h1 + pm + extra
    h2 = md5(s)
    s = pm + key + h1 + pm + h2 + minute + extra
    h3 = md5(s)
    s = pm + key + h1 + pm + h2 + minute + h3 + key + extra
    return md5(s)

# 在 4 个拼接点分别插入 extra
for d in [-1, 0]:
    for cf in cert_forms + [AID, SDK]:
        # 单独插入到每个位置
        for pos in range(4):
            def mk(ts, pos=pos, cf=cf, d=d):
                pm = chr((ord(path[0]) + d) & 0xFF) + path[1:]
                minute = str(ts // 60)
                parts = [pm, key, "", "", minute, ""]
                # 在位置 pos 插入 extra
                s = pm + key + (cf if pos == 0 else "")
                h1 = md5(s)
                s = pm + key + h1 + pm + (cf if pos == 1 else "")
                h2 = md5(s)
                s = pm + key + h1 + pm + h2 + minute + (cf if pos == 2 else "")
                h3 = md5(s)
                s = pm + key + h1 + pm + h2 + minute + h3 + key + (cf if pos == 3 else "")
                return md5(s)
            if check_all(mk, "d=%d pos=%d extra=%s" % (d, pos, cf[:12])):
                raise SystemExit

print("未命中")
