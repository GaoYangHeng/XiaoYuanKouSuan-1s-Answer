import hashlib, itertools

KEY = "wdi4n2t8edr"
AID = "39c0141952095d9c"
PATH = "/leo-game-pk/android/math/pk/match/v2"

# 测试 APK 的 sign（真机，SecureStub 返回 39c0141952095d9c 但可能反射链没走到）
TEST = [
    (1788059164, "a23243656982588c5eb30e7b3af3ecb6"),
    (1788059228, "d25bfb9ea38442e48167f50641e56d2c"),
    (1788059354, "b2a25671a2404816a33ee663332cdcfe"),
    (1788059447, "2ef9b4f9f3836a20ceaeef2d03e654b3"),
    (1788059616, "418b7cede5baf80fff3482117407a641"),
]
# 抓包样本（真实 App）
REAL = [
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

# 时间戳变体
def ts_variants(epoch):
    out = [str(epoch), str(epoch // 60), str(epoch // 60 * 60)]
    import datetime
    dt = datetime.datetime.fromtimestamp(epoch)
    for f in ["%Y%m%d%H%M", "%Y%m%d%H%M%S", "%Y%m%d", "%H%M", "%m%d%H%M", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"]:
        out.append(dt.strftime(f))
    return list(dict.fromkeys(out))

SEPS = ["", "&", "|", "-", "_", "/", ":", ",", "+"]

# 对测试 APK 样本，暴力尝试：device 为空 或 android_id，拼接 path+key+device+ts
def brute(samples, devices, label):
    for epoch, target in samples:
        hit = None
        for t in ts_variants(epoch):
            for dev in devices:
                items = [PATH, KEY, dev, t]
                for perm in itertools.permutations(range(4)):
                    for sep in SEPS:
                        cand = sep.join(items[i] for i in perm)
                        if md5(cand) == target:
                            hit = cand
                            break
                    if hit: break
                if hit: break
            if hit: break
        print(f"[{label}] {'命中' if hit else '未命中'} ts={epoch} {hit!r}")

print("\n=== 测试APK：device 为空 ===")
brute(TEST, [""], "TEST空")
print("\n=== 测试APK：device=android_id ===")
brute(TEST, [AID], "TEST_AID")
print("\n=== 测试APK：device=TEST_DEVICE_ID_FAKE ===")
brute(TEST, ["TEST_DEVICE_ID_FAKE"], "TEST_FAKE")

# 嵌套：sign = MD5(path + key + MD5(device) + ts)
def brute_nested(samples, devices, label):
    for epoch, target in samples:
        hit = None
        for t in ts_variants(epoch):
            for dev in devices:
                devh = md5(dev)
                items = [PATH, KEY, devh, t]
                for perm in itertools.permutations(range(4)):
                    for sep in SEPS:
                        cand = sep.join(items[i] for i in perm)
                        if md5(cand) == target:
                            hit = cand
                            break
                    if hit: break
                if hit: break
            if hit: break
        print(f"[{label}] {'命中' if hit else '未命中'} ts={epoch} {hit!r}")

print("\n=== 嵌套MD5：sign=MD5(path+key+MD5(device)+ts)，device=android_id ===")
brute_nested(REAL, [AID], "REAL嵌套")
print("\n=== 嵌套MD5：测试APK，device=android_id ===")
brute_nested(TEST, [AID], "TEST嵌套")
