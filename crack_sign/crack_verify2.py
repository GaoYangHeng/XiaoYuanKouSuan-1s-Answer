# NOTE: the capture/sample data this script depends on was removed from the repo. Kept for archive/reference only.
# -*- coding: utf-8 -*-
# 决定性纯 Python 验证（零手机/零模拟器）：
# A) 用模拟器已知 h1=1a5fb800... 钉死 P' 变换（首点 vs 全斜杠替换 vs 原样）
# B) dump 5 条真实 URL 参数值
# C) 真实 sign × str变体 × P'变换 × T候选 全枚举
# D) signprobe 真机样本对照（预期 miss -> 证实输出依赖环境/证书）
import json, hashlib, re

JP = r"f:\traework_main workspace\xiaoyuan-kousuan-re\capture\pk_traffic.jsonl"
KEY = "wdi4n2t8edr"
PATH = "/leo-game-pk/android/math/pk/match/v2"
EMU_H1 = "1a5fb8009f1bb35707eae6450440ee76"
EMU_TS = 1788059164
EMU_SIGN = "789f847243914a787764055f39972f4d"

def md5s(s):
    if isinstance(s, str):
        s = s.encode()
    return hashlib.md5(s).hexdigest()

def chain(P, K, T):
    h1 = md5s(P + K)
    h2 = md5s(P + K + h1 + P)
    h3 = md5s(P + K + h1 + P + h2 + T)
    return md5s(P + K + h1 + P + h2 + T + h3 + K)

print("=" * 78)
print("A) P' 变换判定（对照模拟器 h1=%s / final=%s）" % (EMU_H1, EMU_SIGN))
PVARS = {
    "首点": "." + PATH[1:],
    "全斜杠替换": PATH.replace("/", "."),
    "原样": PATH,
    "点前缀不去斜杠": "." + PATH,
}
hitP = None
for name, P in PVARS.items():
    h1 = md5s(P + KEY)
    f = chain(P, KEY, str(EMU_TS // 60))
    mark = []
    if h1 == EMU_H1:
        mark.append("h1命中!")
        hitP = P
    if f == EMU_SIGN:
        mark.append("final命中!")
        hitP = P
    print("  %-8s h1=%s final=%s %s" % (name, h1[:16] + "...", f[:16] + "...", " ".join(mark)))

print("=" * 78)
print("B) 5 条真实 URL 全文")
samples = []
seen = set()
with open(JP, "r", encoding="utf-8-sig") as fh:
    for line in fh:
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
        m = re.search(r"[?&]sign=([a-f0-9]{32})", url)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        jump = re.search(r"jumpTime=(\d+)", obj.get("headers", {}).get("referer", ""))
        samples.append({"url": url, "sign": m.group(1),
                        "jump": int(jump.group(1)) if jump else None})
for i, s in enumerate(samples):
    print("  #%d jump=%s" % (i, s["jump"]))
    print("      url=%s" % s["url"])

print("=" * 78)
print("C) 真实 sign 枚举（str × P' × T）")
def strvars(url):
    base, _, q = url.partition("?")
    host = base[: base.find("/", 8)]
    pathq = base[base.find("/", 8):]
    params = [p for p in q.split("&") if p]
    nosign = "&".join(p for p in params if not p.startswith("sign="))
    out = {
        "path": pathq,
        "path+q(nosign)": pathq + ("?" + nosign if nosign else ""),
        "full(nosign)": host + pathq + ("?" + nosign if nosign else ""),
    }
    return out

TCANDS = ["0", "1", "2", "-1", "-2"]
for s in samples:
    if s["jump"]:
        js = s["jump"] // 1000
        TCANDS += [str(js // 60), str(js)]
hits = 0
for s in samples:
    for sk, sv in strvars(s["url"]).items():
        for pn, P in PVARS.items():
            for T in set(TCANDS):
                if chain(P, KEY, T) == s["sign"]:
                    hits += 1
                    print("  命中! sign=%s str=%s P'=%s T=%s" % (s["sign"], sk, pn, T))
if not hits:
    print("  C) 全部未命中")

print("=" * 78)
print("D) signprobe 真机样本对照（预期 miss -> 证实环境依赖）")
SP = [(1788059164, "c09aca9582fbe0a788022afbcba3e4af"),
      (1788059228, "95b23547d8c598bc3df4f484620abb49"),
      (1788059354, "a8a69657806a8e639a9c0832225bb405")]
for ts, sig in SP:
    r = []
    for pn, P in PVARS.items():
        for T in (str(ts // 60), str(ts)):
            r.append((pn, T, chain(P, KEY, T)))
    ok = [x for x in r if x[2] == sig]
    print("  ts=%d 真机=%s -> %s" % (ts, sig[:16] + "...", ("命中 %s" % (ok[0][:2],)) if ok else "miss(环境依赖证实)"))
