import hashlib

path = "/leo-game-pk/android/math/pk/match/v2"
key = "wdi4n2t8edr"

# FENBI 签名 DER hex
device = open(r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\device_id.txt").read().strip()

def md5(s):
    return hashlib.md5(s.encode()).hexdigest()

def make_sign(p, k, ts, delta):
    pm = chr((ord(p[0]) + delta) & 0xFF) + p[1:]
    minute = str(ts // 60)
    s = pm + k
    h1 = md5(s)
    s = pm + k + h1 + pm
    h2 = md5(s)
    s = pm + k + h1 + pm + h2 + minute
    h3 = md5(s)
    s = pm + k + h1 + pm + h2 + minute + h3 + k
    return md5(s)

# 模拟的配置：FENBI + ts=1788059615 + delta=-1
sign = make_sign(path, key, 1788059615, -1)
print("计算 sign:", sign)
print("模拟 sign: e0302beeadb745ecbbfeb2e8f86d426d")
print("匹配:", sign == "e0302beeadb745ecbbfeb2e8f86d426d")

# 验证 hex1
hex1 = md5(device)
print("\nhex1 = MD5(device) =", hex1)
print("模拟 hex1 = 1dcd877d86d19882d8d055a1a87de93c")
