# NOTE: the capture/sample data this script depends on was removed from the repo. Kept for archive/reference only.
# -*- coding: utf-8 -*-
# 核对 ground truth：pk/match 请求的完整 URL / sign / ts 参数对应关系
import json, re

path = r"f:\traework_main workspace\xiaoyuan-kousuan-re\capture\pk_traffic.jsonl"
rows = []
with open(path, "r", encoding="utf-8-sig") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        url = obj.get("url", "")
        if "pk/match" not in url:
            continue
        u = url.split("?")
        base = u[0]
        q = u[1] if len(u) > 1 else ""
        params = dict(p.split("=", 1) for p in q.split("&") if "=" in p)
        rows.append({
            "obj_ts": obj.get("ts"),
            "type": obj.get("type"),
            "base": base,
            "sign": params.get("sign"),
            "ts_param": params.get("ts"),
            "other_keys": [k for k in params if k not in ("sign", "ts")],
            "body_len": len(obj.get("request_body") or ""),
        })

print("共 %d 条 pk/match 请求" % len(rows))
print()
for i, r in enumerate(rows[:12]):
    print("#%d obj_ts=%s type=%s" % (i, r["obj_ts"], r["type"]))
    print("   base = %s" % r["base"])
    print("   sign = %s" % r["sign"])
    print("   ts_param = %s   其他参数: %s" % (r["ts_param"], r["other_keys"]))
print()
# 交叉核对：ts_param 与 sign 是否每条都成对出现
pairs = set((r["ts_param"], r["sign"]) for r in rows)
print("去重后 (ts_param, sign) 组合数：%d" % len(pairs))
for tp, sg in sorted(pairs, key=lambda x: str(x[0]))[:20]:
    print("   ts_param=%s  sign=%s" % (tp, sg))
