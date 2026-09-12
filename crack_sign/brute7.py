import hashlib
import itertools

KEY = "wdi4n2t8edr"
PATH = "/leo-game-pk/android/math/pk/match/v2"

# 设备 ID 候选（多种表示）
DEVICES = [
    "39c0141952095d9c",      # 疑似 Android ID（之前会话）
    "8368bffb904b9123",      # YFD_U 的 hex
    "14e91d58",              # ks_deviceid 的 hex
    "350821720",             # ks_deviceid 十进制
    "623751490",             # userid
    "DUcQeOjU71a2CBsqifH5VYmGHNyI2E4i8tg2",  # 数盟 did
]

SAMPLES = [
    (1788059164, "7ccaf869bade9bf18c8f0c3e8a034e23"),
    (1788059228, "cfe580fae28fc66c89610b620c815478"),
    (1788059354, "f56ed48991777ba7c272d97167a2619c"),
    (1788059447, "901574426bac0e001f8ffbf46883b9c0"),
    (1788059616, "8f8118bb867adacf8eecc9c8c139f8b1"),
]

SEPS = ["", "&", "|", "-", "_", "/", ":", ",", "=", "+", "@", "#", ".", "~"]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def ts_of(sec, mode):
    m = sec // 60
    if mode == "minute":
        return str(m)
    if mode == "seconds":
        return str(sec)
    if mode == "floored":
        return str(sec - sec % 60)
    if mode == "minute_x60":
        return str(m * 60)
    return str(m)


def permutations(parts):
    n = len(parts)
    for p in itertools.permutations(range(n)):
        yield p


def check_candidate(pool, mode):
    """pool: list of component strings (含占位 ts). 校验全部样本"""
    n = len(pool)
    for perm in itertools.permutations(range(n)):
        ordered = [pool[i] for i in perm]
        for sep in SEPS:
            cand = sep.join(ordered)
            # 用样本0的 ts 占位替换，然后逐样本验证
            t0 = ts_of(SAMPLES[0][0], mode)
            ok = True
            for sec, sign in SAMPLES:
                tv = ts_of(sec, mode)
                cc = cand.replace(t0, tv, 1)
                if md5(cc) != sign:
                    ok = False
                    break
            if ok:
                return cand
    return None


def main():
    modes = ["minute", "seconds", "floored", "minute_x60"]
    for dev in DEVICES:
        md5dev = md5(dev)
        for mode in modes:
            t0 = ts_of(SAMPLES[0][0], mode)
            # 纯拼接
            pools = [
                [PATH, KEY, t0, dev],
                [PATH, KEY, dev, t0],
                [KEY, PATH, t0, dev],
                [dev, PATH, KEY, t0],
                [PATH, t0, KEY, dev],
                [KEY, t0, PATH, dev],
            ]
            for pool in pools:
                r = check_candidate(pool, mode)
                if r:
                    print(f"[命中-拼接] dev={dev!r} mode={mode} -> {r!r}")
                    return
            # 嵌套：device_id 先 MD5
            pools2 = [
                [PATH, KEY, t0, md5dev],
                [PATH, KEY, md5dev, t0],
                [KEY, PATH, t0, md5dev],
                [md5dev, PATH, KEY, t0],
                [PATH, md5dev, t0, KEY],
            ]
            for pool in pools2:
                r = check_candidate(pool, mode)
                if r:
                    print(f"[命中-嵌套dev] dev={dev!r} mode={mode} -> {r!r}")
                    return
            # 内层 MD5(path+key) 等
            for inner in [PATH + KEY, KEY + PATH, PATH + dev, KEY + dev, PATH + KEY + dev]:
                h = md5(inner)
                pools3 = [
                    [h, t0, dev],
                    [h, t0, md5dev],
                    [PATH, h, t0],
                    [h, dev, t0],
                ]
                for pool in pools3:
                    r = check_candidate(pool, mode)
                    if r:
                        print(f"[命中-内层] dev={dev!r} inner={inner!r} mode={mode} -> {r!r}")
                        return
    print("全部未命中")


if __name__ == "__main__":
    main()
