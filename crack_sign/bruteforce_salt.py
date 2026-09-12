import hashlib, itertools

KEY = "wdi4n2t8edr"
AID = "39c0141952095d9c"
PATH = "/leo-game-pk/android/math/pk/match/v2"
S1 = "9a2806e869bf45f85e601a69f895d2131dcd877d86d19882d"
S2 = "1dcd877d86d19882d8d055a1a87de93czcvsd1wr2tc"

SAMPLES = [
    (1788059164, "7ccaf869bade9bf18c8f0c3e8a034e23"),
    (1788059228, "cfe580fae28fc66c89610b620c815478"),
    (1788059354, "f56ed48991777ba7c272d97167a2619c"),
    (1788059447, "901574426bac0e001f8ffbf46883b9c0"),
    (1788059616, "8f8118bb867adacf8eecc9c8c139f8b1"),
]

def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()

hex1 = md5(AID)
print(f"MD5(device) = {hex1}")

# 时间戳变体
def ts_variants(epoch):
    out = [str(epoch), str(epoch // 60), str(epoch // 60 * 60)]
    import datetime
    dt = datetime.datetime.fromtimestamp(epoch)
    for f in ["%Y%m%d%H%M", "%Y%m%d%H%M%S", "%Y%m%d", "%H%M", "%m%d%H%M"]:
        out.append(dt.strftime(f))
    return list(dict.fromkeys(out))

SEPS = ["", "&", "|", "-", "_", "/", ":", ",", "+"]

def brute(samples, items, label, max_perm=None):
    for epoch, target in samples:
        hit = None
        for t in ts_variants(epoch):
            it = list(items) + [t]
            n = len(it)
            perms = itertools.permutations(range(n))
            for perm in perms:
                for sep in SEPS:
                    cand = sep.join(it[i] for i in perm)
                    if md5(cand) == target:
                        hit = cand
                        break
                if hit:
                    break
            if hit:
                break
        print(f"[{label}] {'命中!' if hit else '未命中'} ts={epoch} {hit!r}")
        if hit:
            return hit
    return None

# 尝试 1：path + key + hex1 + 时间戳（含 path[0] 修改）
# 先试无 s1/s2
print("\n=== 尝试：path,key,hex1,ts（无盐值）===")
brute(SAMPLES, [PATH, KEY, hex1], "无盐")

# 尝试 2：加 s1
print("\n=== 尝试：path,key,hex1,s1,ts ===")
brute(SAMPLES, [PATH, KEY, hex1, S1], "含s1")

# 尝试 3：加 s2
print("\n=== 尝试：path,key,hex1,s2,ts ===")
brute(SAMPLES, [PATH, KEY, hex1, S2], "含s2")

# 尝试 4：加 s1 前32 + s2 前32
print("\n=== 尝试：path,key,hex1,s1[:32],s2[:32],ts ===")
brute(SAMPLES, [PATH, KEY, hex1, S1[:32], S2[:32]], "含s1_32_s2_32")
