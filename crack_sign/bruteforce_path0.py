import hashlib, itertools

KEY = "wdi4n2t8edr"
AID = "39c0141952095d9c"
PATH = "/leo-game-pk/android/math/pk/match/v2"

SAMPLES = [
    (1788059164, "7ccaf869bade9bf18c8f0c3e8a034e23"),
    (1788059228, "cfe580fae28fc66c89610b620c815478"),
]

def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()

hex1 = md5(AID)

# 计算 memcmp(s1, hex1) 和 memcmp(s2, hex1)（这里简化：第一个不同字节差值）
S1 = "9a2806e869bf45f85e601a69f895d2131dcd877d86d19882d"
S2 = "1dcd877d86d19882d8d055a1a87de93czcvsd1wr2tc"
def memcmp_bytes(a, b):
    for x, y in zip(a.encode(), b.encode()):
        if x != y:
            return x - y
    return len(a) - len(b)

m1 = memcmp_bytes(S1, hex1)
m2 = memcmp_bytes(S2, hex1)
print(f"memcmp(s1,hex1)={m1}, memcmp(s2,hex1)={m2}")

# r4 = -11*r8 - 12（假设 r8 未知）
# 直接暴力 path[0] 的 256 种修改
SEPS = ["", "&", "|", "-", "_", "/", ":", ",", "+"]
def ts_variants(epoch):
    import datetime
    out = [str(epoch), str(epoch // 60), str(epoch // 60 * 60)]
    dt = datetime.datetime.fromtimestamp(epoch)
    for f in ["%Y%m%d%H%M", "%Y%m%d%H%M%S", "%Y%m%d", "%H%M", "%m%d%H%M"]:
        out.append(dt.strftime(f))
    return list(dict.fromkeys(out))

def brute_path0(samples, items, label):
    for epoch, target in samples:
        hit = None
        for t in ts_variants(epoch):
            it = list(items) + [t]
            n = len(it)
            for k in range(256):
                p = chr(k) + PATH[1:]
                it[0] = p  # 假设 path 是第 0 个元素
                # 但 path 可能不在第 0 个位置，需要全排列
                for perm in itertools.permutations(range(n)):
                    for sep in SEPS:
                        cand = sep.join(it[i] for i in perm)
                        if md5(cand) == target:
                            hit = (k, p, cand)
                            break
                    if hit:
                        break
                if hit:
                    break
            if hit:
                break
        print(f"[{label}] {'命中!' if hit else '未命中'} ts={epoch} k={hit[0] if hit else '?'} path0={hit[1]!r} cand={hit[2]!r}" if hit else f"[{label}] 未命中 ts={epoch}")
        if not hit:
            return None
    return hit

# path[0] 修改 + path,key,hex1,ts 拼接
print("\n=== path[0]修改 + path,key,hex1,ts ===")
brute_path0(SAMPLES, [PATH, KEY, hex1], "path0")
