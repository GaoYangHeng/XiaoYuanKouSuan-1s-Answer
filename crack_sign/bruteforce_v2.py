import hashlib
from itertools import permutations

path = "/leo-game-pk/android/math/pk/match/v2"
key = "wdi4n2t8edr"
hex1 = "1dcd877d86d19882d8d055a1a87de93c"  # MD5(签名 DER hex)

# 抓包样本：sign + 抓包时刻（北京 2026-08-30），换算秒时间戳
samples = [
    ("d9a0ede59cd64436379a3d6e716c3f74", 1788084659),
    ("4d4fb91c395b601b9b61816f16420484", 1788084681),
    ("57e40701ec58b4d9c89f471310ad3270", 1788084809),
    ("296bca5eaca63108fd727d1035173222", 1788084859),
    ("03f6ab5174f50e90bce5645947bf11e6", 1788085018),
]

# path[0] 修改量：尝试 delta 0..255（path[0] += delta）
# 时间戳表示：秒 // 60（分钟）
def check(fmt, delta, use_minutes=True):
    # fmt: 元素顺序，如 ("path","key","hex1","ts")
    def elem(name, ts):
        if name == "path":
            p = list(path)
            p[0] = chr((ord(p[0]) + delta) & 0xFF)
            return "".join(p)
        if name == "key":
            return key
        if name == "hex1":
            return hex1
        if name == "ts":
            v = ts // 60 if use_minutes else ts
            return str(v)
        return ""
    for sign, ts in samples:
        parts = "".join(elem(n, ts) for n in fmt)
        if hashlib.md5(parts.encode()).hexdigest() == sign:
            return True
    return False

seps = ["", "&", "|", ":", "/", "-", "_", "?", "=", ",", ";", ".", "+", "*"]
names = ["path", "key", "hex1", "ts"]

found = False
for use_minutes in (True, False):
    for perm in permutations(names):
        for delta in range(0, 256):
            # 无分隔符
            if check(perm, delta, use_minutes):
                print(f"[命中] 无分隔符 fmt={perm} delta={delta} minutes={use_minutes}")
                found = True
                break
            # 有分隔符
            for sep in seps:
                fmt = tuple(x + sep for x in perm[:-1]) + (perm[-1],)
                if check(fmt, delta, use_minutes):
                    print(f"[命中] 分隔符={sep!r} fmt={perm} delta={delta} minutes={use_minutes}")
                    found = True
                    break
        if found:
            break
    if found:
        break

if not found:
    print("未命中（无分隔符 + 常见分隔符 + delta 0..255 + 分钟/秒）")
