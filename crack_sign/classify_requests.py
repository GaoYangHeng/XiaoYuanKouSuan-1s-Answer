# NOTE: the capture/sample data this script depends on was removed from the repo. Kept for archive/reference only.
import json
import re
from urllib.parse import urlsplit, parse_qs

path = r"f:\traework_main workspace\xiaoyuan-kousuan-re\capture\pk_traffic.jsonl"
n_web, n_native = 0, 0
native_samples = []
for line in open(path, "r", encoding="utf-8-sig"):
    line = line.strip()
    if not line:
        continue
    try:
        obj = json.loads(line)
    except Exception:
        continue
    if obj.get("type") != "REQ":
        continue
    ua = obj.get("headers", {}).get("user-agent", "")
    url = obj.get("url", "")
    sp = urlsplit(url)
    q = parse_qs(sp.query)
    sign = q.get("sign", [""])[0]
    if "Chrome/" in ua:
        n_web += 1
        continue
    n_native += 1
    native_samples.append({
        "rec_ts": obj.get("ts"),
        "method": obj.get("method"),
        "path": sp.path,
        "sign": sign,
        "ua": ua[:60],
        "qkeys": list(q.keys())[:12],
    })

print(f"WebView 请求: {n_web}, 原生请求: {n_native}")
print("---- 原生请求样本（前 40 条）----")
for s in native_samples[:40]:
    print(f"{s['rec_ts']} {s['method']} {s['path']} sign={s['sign'][:32]} ua={s['ua']} q={s['qkeys']}")
