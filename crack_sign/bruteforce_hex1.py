import hashlib, itertools

KEY = "wdi4n2t8edr"
AID = "39c0141952095d9c"
PATH = "/leo-game-pk/android/math/pk/match/v2"

# 样本（path, sign, epoch秒）
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
print(f"MD5(android_id) = {hex1}")
print(f"MD5(android_id) 二进制 = {bytes.fromhex(hex1).hex()}")

# 时间戳变体
def ts_variants(epoch):
    out = []
    out.append(str(epoch))            # 秒
    out.append(str(epoch // 60))       # 分钟
    out.append(str(epoch // 60 * 60))  # 分钟对齐
    return list(dict.fromkeys(out))

SEPS = ["", "&", "|", "-", "_", "/", ":", ",", "+"]

# 尝试拼接：path, key, hex1, ts 的排列 + 分隔符
found = []
for epoch, target in SAMPLES:
    tsvals = ts_variants(epoch)
    hit = None
    for t in tsvals:
        items = [PATH, KEY, hex1, t]
        for perm in itertools.permutations([0, 1, 2, 3]):
            for sep in SEPS:
                cand = sep.join(items[i] for i in perm)
                if md5(cand) == target:
                    hit = cand
                    break
            if hit:
                break
        if hit:
            break
    print(f"{'[命中]' if hit else '[未命中]'} ts={epoch} {hit!r}")

# 也尝试 hex1 用二进制（bytes 拼接）
for epoch, target in SAMPLES:
    tsvals = ts_variants(epoch)
    hit = None
    b_hex1 = bytes.fromhex(hex1)
    for t in tsvals:
        t_b = t.encode()
        parts = [PATH.encode(), KEY.encode(), b_hex1, t_b]
        for perm in itertools.permutations(range(4)):
            cand = b"".join(parts[i] for i in perm)
            if hashlib.md5(cand).hexdigest() == target:
                hit = cand
                break
        if hit:
            break
    print(f"[二进制拼接]{'[命中]' if hit else '[未命中]'} ts={epoch} {hit!r}")
