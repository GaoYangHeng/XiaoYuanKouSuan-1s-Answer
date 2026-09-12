# NOTE: the capture/sample data this script depends on was removed from the repo. Kept for archive/reference only.
# -*- coding: utf-8 -*-
# 从 flows.mitm 提取全部 xyks 请求样本 -> sign_samples.json + 统计
import json, re
from urllib.parse import urlsplit, unquote
from mitmproxy import io

FLOW_FILE = r"f:\traework_main workspace\xiaoyuan-kousuan-re\flows.mitm"
OUT_FILE = r"f:\traework_main workspace\xiaoyuan-kousuan-re\sign_samples.json"

samples = []
with open(FLOW_FILE, "rb") as fp:
    reader = io.FlowReader(fp)
    for flow in reader.stream():
        try:
            req = flow.request
            host = req.pretty_host
            if "yuanfudao.com" not in host:
                continue
            u = urlsplit(req.pretty_url)
            # 从 query 中剥离 sign
            qsign = ""
            qparts = []
            for kv in u.query.split("&"):
                if kv.startswith("sign="):
                    qsign = kv[5:]
                else:
                    qparts.append(kv)
            qclean = "&".join(qparts)
            ts_ms = req.headers.get("x-xyks-req-timestamp", "")
            body = ""
            if req.content:
                body = req.get_text(strict=False) or ""
            samples.append({
                "method": req.method,
                "host": host,
                "path": u.path,
                "query": qclean,
                "sign": qsign,
                "ts_ms": ts_ms,
                "body": body,
                "blen": len(body),
                "status": flow.response.status_code if flow.response else 0,
            })
        except Exception as e:
            print("ERR", e)

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(samples, f, ensure_ascii=False, indent=1)

# ---- 统计 ----
print("total samples:", len(samples))
paths = {}
for s in samples:
    paths.setdefault(s["path"], []).append(s)
print("unique paths:", len(paths))

# 1) 同 path 多样本：验证「同分钟同 sign」
print("\n== per-path duplicates ==")
for p, ss in sorted(paths.items(), key=lambda x: -len(x[1])):
    if len(ss) < 2:
        continue
    print(f"\n{p}  n={len(ss)}")
    for s in ss[:12]:
        ts = int(s["ts_ms"]) // 1000 if s["ts_ms"] else 0
        print(f"  ts={ts} minute={ts//60} sign={s['sign']} blen={s['blen']} status={s['status']}")

# 2) 同一分钟内不同 path：sign 是否不同
print("\n== same-minute cross-path ==")
bymin = {}
for s in samples:
    if not s["ts_ms"] or not s["sign"]:
        continue
    ts = int(s["ts_ms"]) // 1000
    bymin.setdefault(ts // 60, []).append(s)
for m in sorted(bymin):
    ss = bymin[m]
    signs = set(x["sign"] for x in ss)
    if len(ss) > 1:
        print(f"minute={m} n={len(ss)} uniq_sign={len(signs)}")
        for s in ss[:10]:
            print(f"   {s['method']} {s['path']} sign={s['sign']} blen={s['blen']}")
