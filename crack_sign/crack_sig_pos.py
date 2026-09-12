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

# 签名各种形式
CERT_MD5 = "da8e2ec9722dee7ab20752a92e588667"           # md5(cert)
CERT_SHA256 = "cae28ac067e030162deac0a65394717a6d89066d906f80631eb800ae3d16c8bf"
CERT_MD5_HEXSTR = "3779f66ceb0767431ab9c507679fba98"    # md5(cert DER hex字符串)
AID = "39c0141952095d9c"
AID_MD5 = md5(AID)                                      # md5(android_id)
SDK = "34"

sig_forms = [CERT_MD5, CERT_SHA256, CERT_MD5_HEXSTR, AID, AID_MD5, SDK]

def check(fn):
    return sum(1 for ts, sig in samples if fn(ts) == sig)

def ts_variants(ts):
    return [str(ts), str(ts // 60), str(ts // 600), str(ts % 60)]

# make_sign 4 轮结构，签名 sig 替换/插入到各位置
def make_variant(ts, sig, d, ts_idx, sig_pos):
    pm = chr((ord(path[0]) + d) & 0xFF) + path[1:]
    T = ts_variants(ts)[ts_idx]
    # 元素池：pm, key, sig, T（sig 插入到 sig_pos 个拼接点）
    s = pm + key + (sig if sig_pos == 0 else "")
    h1 = md5(s)
    s = pm + key + h1 + pm + (sig if sig_pos == 1 else "")
    h2 = md5(s)
    s = pm + key + h1 + pm + h2 + T + (sig if sig_pos == 2 else "")
    h3 = md5(s)
    s = pm + key + h1 + pm + h2 + T + h3 + key + (sig if sig_pos == 3 else "")
    return md5(s)

for d in range(-3, 4):
    for sf in sig_forms:
        for ti in range(4):
            for sp in range(4):
                ok = check(lambda ts, sf=sf, d=d, ti=ti, sp=sp: make_variant(ts, sf, d, ti, sp))
                if ok >= 3:
                    print("HIT d=%d sig=%s ti=%d sp=%d" % (d, sf[:12], ti, sp))
                    raise SystemExit

# 签名替换 pm / key / T
for d in range(-3, 4):
    for sf in sig_forms:
        for ti in range(4):
            pm = chr((ord(path[0]) + d) & 0xFF) + path[1:]
            T = ts_variants(1788059164)[ti]
            # 签名替换 pm
            def f1(ts, sf=sf, d=d, ti=ti):
                pm = chr((ord(path[0]) + d) & 0xFF) + path[1:]
                T = ts_variants(ts)[ti]
                s = sf + key; h1 = md5(s)
                s = sf + key + h1 + sf; h2 = md5(s)
                s = sf + key + h1 + sf + h2 + T; h3 = md5(s)
                s = sf + key + h1 + sf + h2 + T + h3 + key
                return md5(s)
            if check(f1) >= 3:
                print("HIT sig替换pm d=%d sf=%s ti=%d" % (d, sf[:12], ti)); raise SystemExit
            # 签名替换 key
            def f2(ts, sf=sf, d=d, ti=ti):
                pm = chr((ord(path[0]) + d) & 0xFF) + path[1:]
                T = ts_variants(ts)[ti]
                s = pm + sf; h1 = md5(s)
                s = pm + sf + h1 + pm; h2 = md5(s)
                s = pm + sf + h1 + pm + h2 + T; h3 = md5(s)
                s = pm + sf + h1 + pm + h2 + T + h3 + sf
                return md5(s)
            if check(f2) >= 3:
                print("HIT sig替换key d=%d sf=%s ti=%d" % (d, sf[:12], ti)); raise SystemExit

print("未命中")
