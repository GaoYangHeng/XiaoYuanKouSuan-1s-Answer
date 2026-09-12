import hashlib
import itertools

path = "/leo-game-pk/android/math/pk/match/v2"
key = "wdi4n2t8edr"

# minute 差分样本（隔离出 minute 变量）
samples = [
    (29800986, "43e5d8c692b910efa33aa79e86564605"),  # 1788059160//60
    (29800987, "d7ffe1841b485e53854308ab55d6754b"),  # 1788059220//60
    (29800989, "a8a69657806a8e639a9c0832225bb405"),  # 1788059354//60
]

def md5(s):
    if isinstance(s, str):
        s = s.encode()
    return hashlib.md5(s).hexdigest()

# 签名各种形式（Test 签名）
CERT_MD5 = "da8e2ec9722dee7ab20752a92e588667"
CERT_SHA256 = "cae28ac067e030162deac0a65394717a6d89066d906f80631eb800ae3d16c8bf"
CERT_MD5_HEXSTR = "3779f66ceb0767431ab9c507679fba98"  # md5(证书DER hex字符串)
AID = "39c0141952095d9c"
AID_MD5 = md5(AID)
SDK = "34"

sig_forms = [CERT_MD5, CERT_SHA256, CERT_MD5_HEXSTR, AID, AID_MD5, SDK]

def build(P, K, T):
    s = P
    s = s + K
    s = s + s
    s = s + P
    s = s + s
    s = s + T
    s = s + s
    s = s + K
    return s

def check(fn):
    return sum(1 for m, sig in samples if fn(m) == sig)

# T 的表示
def t_forms(m):
    return [str(m), hex(m)[2:], hex(m)[2:].upper()]

hits = 0
# 系统化搜索 P、K、T
for sf in sig_forms:
    P_forms = [path, sf, path + sf, sf + path]
    K_forms = [key, sf, sf + key, key + sf]
    for P in P_forms:
        for K in K_forms:
            for tfi in range(3):
                def fn(m, P=P, K=K, tfi=tfi):
                    return md5(build(P, K, t_forms(m)[tfi]))
                ok = check(fn)
                if ok >= 3:
                    print("HIT P=%s K=%s tfi=%d" % (P[:20], K[:20], tfi))
                    hits += 1

if hits == 0:
    print("未命中 build 序列")
