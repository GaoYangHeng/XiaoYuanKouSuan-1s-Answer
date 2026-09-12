# NOTE: the capture/sample data this script depends on was removed from the repo. Kept for archive/reference only.
# -*- coding: utf-8 -*-
# 用真实抓包样本（5 条 pk/match）+ 真实 query + jumpTime 全枚举验证 sign 公式
# 链结构（模拟器实锤）：h1=md5(P'+K); h2=md5(P'+K+h1+P'); h3=md5(P'+K+h1+P'+h2+T); sign=md5(...+h3+K)
import json, hashlib, re, itertools

JP = r"f:\traework_main workspace\xiaoyuan-kousuan-re\capture\pk_traffic.jsonl"
KEY = "wdi4n2t8edr"
PATH_ONLY = "/leo-game-pk/android/math/pk/match/v2"

def md5s(s):
    if isinstance(s, str):
        s = s.encode("utf-8")
    return hashlib.md5(s).hexdigest()

# 1) 解析全部 pk/match REQ 样本
samples = []
seen_sign = set()
with open(JP, "r", encoding="utf-8-sig") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if "pk/match" not in obj.get("url", "") or obj.get("type") != "REQ":
            continue
        url = obj["url"]
        sign = re.search(r"[?&]sign=([a-f0-9]{32})", url)
        jump = re.search(r"jumpTime=(\d+)", obj.get("headers", {}).get("referer", ""))
        if not sign:
            continue
        sg = sign.group(1)
        if sg in seen_sign:
            continue
        seen_sign.add(sg)
        base, _, q = url.partition("?")
        # query 参数列表（保序），sign 前缀区分
        params = [p for p in q.split("&") if p]
        no_sign = "&".join(p for p in params if not p.startswith("sign="))
        with_sign = "&".join(params)
        host = base[: base.find("/", 8)]
        pathq = base[base.find("/", 8):]
        samples.append({
            "obj_ts": obj.get("ts"),
            "sign": sg,
            "jump_ms": int(jump.group(1)) if jump else None,
            "path": base[base.find("/", 8):],
            "path_nosign": pathq + ("?" + no_sign if no_sign else ""),
            "path_sign": pathq + "?" + with_sign,
            "full_nosign": host + pathq + ("?" + no_sign if no_sign else ""),
            "full_sign": url,
        })

print("样本数（去重 sign）：%d" % len(samples))
for s in samples:
    print("  obj_ts=%s jump_ms=%s sign=%s" % (s["obj_ts"], s["jump_ms"], s["sign"]))
print()

# 2) 枚举
def chain_v1(P, K, T):
    h1 = md5s(P + K)
    h2 = md5s(P + K + h1 + P)
    h3 = md5s(P + K + h1 + P + h2 + T)
    return md5s(P + K + h1 + P + h2 + T + h3 + K)

def pvariants(s):
    out = set()
    if s.startswith("/"):
        out.add("." + s[1:])
    out.add("." + s)
    out.add(s)
    return out

STR_KEYS = ["path", "path_nosign", "path_sign", "full_nosign", "full_sign"]
hits = []
for s in samples:
    # T 候选：jumpTime 秒 ±3 与 obj_ts 相对秒（以第一条 jump 推日期）
    tseeds = set()
    if s["jump_ms"]:
        js = s["jump_ms"] // 1000
        tseeds.update(range(js - 3, js + 4))
        tseeds.add((s["jump_ms"] + 500) // 1000)
    Tcands = set()
    for ts in tseeds:
        Tcands.add(str(ts // 60))
        Tcands.add(str(ts))
    for sk in STR_KEYS:
        for P in pvariants(s[sk]):
            for T in Tcands:
                if chain_v1(P, KEY, T) == s["sign"]:
                    hits.append((s["sign"], sk, P[:60], T))
                    print("命中！sign=%s  str字段=%s  P'=%s...  T=%s" % (s["sign"], sk, P[:40], T))

print()
if hits:
    print("共命中 %d 条" % len(hits))
else:
    print("V1 链未命中。转扩展枚举：K 位置变体 / T 直接用秒 / P' 无点前缀 / body 时间 …")
    # 扩展：对样本1 做更暴力的小空间穷举（结构变体 x P 变体 x T 变体）
    s = samples[0]
    tseeds = set()
    if s["jump_ms"]:
        js = s["jump_ms"] // 1000
        tseeds.update(range(js - 5, js + 6))
    tvars = set()
    for ts in tseeds:
        tvars.add(str(ts // 60)); tvars.add(str(ts)); tvars.add(str(ts % 60)); tvars.add(str(ts // 600))
    pvars = set()
    for sk in STR_KEYS:
        pvars |= pvariants(s[sk])
        pvars.add(s[sk])
    kvars = [KEY, KEY.upper(), KEY[::-1]]
    structs = [
        lambda P,K,T: md5s(P+K+md5s(P+K)+P+md5s(P+K+md5s(P+K)+P)+T),
        lambda P,K,T: md5s(md5s(P+K)+P+T),
        lambda P,K,T: md5s(P+K+T),
        lambda P,K,T: md5s(T+P+K),
    ]
    cnt = 0
    for P in pvars:
        for K in kvars:
            for T in tvars:
                for i, fn in enumerate(structs):
                    cnt += 1
                    if fn(P, K, T) == s["sign"]:
                        print("扩展命中！struct=%d P'=%s... K=%s T=%s" % (i+1, P[:40], K, T))
    print("扩展枚举完成，共 %d 组合，未再命中则需回到模拟器取真实 str 输入" % cnt)
