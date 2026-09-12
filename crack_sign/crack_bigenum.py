# -*- coding: utf-8 -*-
# 大范围 T 枚举（纯 Python，零模拟器）：
# 背景：真实 app ts = x.k().s()/1000 = time.delta/1000（服务器时钟差秒），
#       不等于抓包时间戳分钟！time.delta 未知 → T 可能偏移任意量。
# 策略：T ∈ [base-12h, base+12h]（分钟粒度）+ 秒粒度邻域 + 小整数候选
#       P' 候选覆盖 path/query/full 全部变换
import hashlib

KEY = "wdi4n2t8edr"
PATH = "/leo-game-pk/android/math/pk/match/v2"
Q_NS = ("pointId=1951&triggerPeakMatch=0&_productId=611&platform=android34"
        "&version=3.141.1&vendor=hihonor&av=5&deviceCategory=phone"
        "&webviewVersion=131&whRatio=2.06")
FULL_NS = "https://xyks.yuanfudao.com" + PATH + "?" + Q_NS

def md5s(b):
    return hashlib.md5(b).hexdigest()

P_PRIMES = {
    "path_dot":    "." + PATH[1:],
    "path_alldot": PATH.replace("/", "."),
    "path_raw":    PATH,
    "path_dotkeep":"." + PATH,
    "q_dot":       "." + Q_NS,
    "q_raw":       Q_NS,
    "full_dot":    "." + FULL_NS[1:],
    "full_alldot": FULL_NS.replace("/", "."),
    "full_raw":    FULL_NS,
}

# 真实 app 5 sign（jumpTime 为抓包 referer 中的本地毫秒时间戳）
REAL = [
    (1788084658334, "d9a0ede59cd64436379a3d6e716c3f74"),
    (1788084680487, "4d4fb91c395b601b9b61816f16420484"),
    (1788084808289, "57e40701ec58b4d9c89f471310ad3270"),
    (1788084858110, "296bca5eaca63108fd727d1035173222"),
    (1788085016916, "03f6ab5174f50e90bce5645947bf11e6"),
]
# signprobe 真机 3 sign（ts 为 logcat 推算，可能不准 → 大范围枚举）
SP = [
    (1788059164, "c09aca9582fbe0a788022afbcba3e4af"),
    (1788059228, "95b23547d8c598bc3df4f484620abb49"),
    (1788059354, "a8a69657806a8e639a9c0832225bb405"),
]

def try_chain(P, T):
    h1 = md5s((P + KEY).encode())
    h2 = md5s((P + KEY + h1 + P).encode())
    pre = P + KEY + h1 + P + h2
    h3 = md5s((pre + T).encode())
    return md5s((pre + T + h3 + KEY).encode())

def enum_T(P, base_minute, span=720):
    """枚举分钟 T = base±span，返回命中的 (T, offset)"""
    h1 = md5s((P + KEY).encode())
    h2 = md5s((P + KEY + h1 + P).encode())
    pre = P + KEY + h1 + P + h2
    for d in range(-span, span + 1):
        t = str(base_minute + d)
        h3 = md5s((pre + t).encode())
        if md5s((pre + t + h3 + KEY).encode()):
            yield t, d, pre

# ---------- signprobe 3 sign：P=path_dot，T ±24h ----------
print("=" * 70)
print("[1] signprobe 3 sign：P'=path_dot，T 枚举 ±24h（分钟）")
for ts0, sg in SP:
    base = ts0 // 60
    found = None
    for d in range(-1440, 1441):
        t = str(base + d)
        if try_chain(P_PRIMES["path_dot"], t) == sg:
            found = (t, d)
            break
    print(f"  guess_ts={ts0}: " + (f"命中 T='{found[0]}' (偏移 {found[1]} 分钟)" if found else "miss"))

# ---------- 真实 5 sign：全 P' × T ±12h ----------
print("=" * 70)
print("[2] 真实 5 sign：全 P' 候选 × T 枚举 ±12h（分钟）")
for jump, sg in REAL:
    base = jump // 1000 // 60
    hits = []
    for pname, P in P_PRIMES.items():
        h1 = md5s((P + KEY).encode())
        h2 = md5s((P + KEY + h1 + P).encode())
        pre = P + KEY + h1 + P + h2
        for d in range(-720, 721):
            t = str(base + d)
            h3 = md5s((pre + t).encode())
            if md5s((pre + t + h3 + KEY).encode()) == sg:
                hits.append((pname, t, d))
    print(f"  jump={jump}: " + (f"命中 {hits}" if hits else "miss"))

# ---------- 真实 5 sign：秒粒度 T（jump//1000 ± 3h）----------
print("=" * 70)
print("[3] 真实 5 sign：秒粒度 T 枚举（P' 全候选，±3h 秒）")
for jump, sg in REAL:
    base_sec = jump // 1000
    hits = []
    for pname, P in P_PRIMES.items():
        h1 = md5s((P + KEY).encode())
        h2 = md5s((P + KEY + h1 + P).encode())
        pre = P + KEY + h1 + P + h2
        for d in range(-10800, 10801):
            t = str(base_sec + d)
            h3 = md5s((pre + t).encode())
            if md5s((pre + t + h3 + KEY).encode()) == sg:
                hits.append((pname, t))
                break
    print(f"  jump={jump}: " + (f"命中 {hits}" if hits else "miss"))

# ---------- 小整数 T 候选（time.delta 极端假设）----------
print("=" * 70)
print("[4] 小整数 T 候选（'0'~'3600' 等分钟值）× 全 P'")
small_Ts = [str(i) for i in range(0, 61)] + [str(i * 60) for i in range(1, 61)]
found_all = []
for sg in {sg for _, sg in REAL} | {sg for _, sg in SP}:
    for pname, P in P_PRIMES.items():
        for t in small_Ts:
            if try_chain(P, t) == sg:
                found_all.append((sg[:8], pname, t))
print("  命中: " + (str(found_all) if found_all else "miss"))

print("=" * 70)
print("枚举完成")
