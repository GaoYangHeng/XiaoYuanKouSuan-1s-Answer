import hashlib, itertools

KEY = "wdi4n2t8edr"
PATH = "/leo-game-pk/android/math/pk/match/v2"

DEVICES = [
    "0123456789abcdef",       # android_id
    "A2NMVB1816014342",       # serialno
    "623751490",              # userid
    "350821720",              # ks_deviceid
    "-8977714769984515805",   # YFD_U
]

SAMPLES = [
    (1788059164, "7ccaf869bade9bf18c8f0c3e8a034e23"),
    (1788059228, "cfe580fae28fc66c89610b620c815478"),
    (1788059354, "f56ed48991777ba7c272d97167a2619c"),
    (1788059447, "901574426bac0e001f8ffbf46883b9c0"),
    (1788059616, "8f8118bb867adacf8eecc9c8c139f8b1"),
]

def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def ts_variants(epoch):
    import datetime
    out = [str(epoch), str(epoch // 60), str(epoch // 60 * 60)]
    dt = datetime.datetime.fromtimestamp(epoch)
    for f in ["%Y%m%d%H%M", "%Y%m%d%H%M%S", "%Y%m%d", "%H%M", "%m%d%H%M", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"]:
        out.append(dt.strftime(f))
    return list(dict.fromkeys(out))

SEPS = ["", "&", "|", "-", "_", "/", ":", ",", "+"]

for dev in DEVICES:
    devh = md5(dev)
    hit_all = True
    found = None
    for epoch, target in SAMPLES:
        hit = None
        for t in ts_variants(epoch):
            # 直接拼接 + 嵌套 MD5
            for dv in [dev, devh]:
                items = [PATH, KEY, dv, t]
                for perm in itertools.permutations(range(4)):
                    for sep in SEPS:
                        cand = sep.join(items[i] for i in perm)
                        if md5(cand) == target:
                            hit = cand
                            break
                    if hit: break
                if hit: break
            if hit: break
        if hit:
            found = hit
        else:
            hit_all = False
        # 只打印命中的
    if hit_all:
        print(f"[命中!] device={dev!r} 拼接={found!r}")
    else:
        # 打印该 device 是否命中第一个样本
        t = str(SAMPLES[0][0])
        h = None
        for tv in ts_variants(SAMPLES[0][0]):
            for dv in [dev, devh]:
                items = [PATH, KEY, dv, tv]
                for perm in itertools.permutations(range(4)):
                    for sep in SEPS:
                        cand = sep.join(items[i] for i in perm)
                        if md5(cand) == SAMPLES[0][1]:
                            h = cand
                            break
                    if h: break
                if h: break
            if h: break
        if h:
            print(f"[部分命中] device={dev!r} {h!r}")
        else:
            print(f"[未命中] device={dev!r}")
