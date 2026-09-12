# NOTE: the capture/sample data this script depends on was removed from the repo. Kept for archive/reference only.
# -*- coding: utf-8 -*-
# dump 一条完整 REQ 记录：所有字段、headers、body——找 sign 算法的真实 ts 来源
import json

path = r"f:\traework_main workspace\xiaoyuan-kousuan-re\capture\pk_traffic.jsonl"
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
        if "pk/match" in url and obj.get("type") == "REQ":
            print("=== 顶层字段 ===")
            for k, v in obj.items():
                if k in ("url", "request_body", "response_body"):
                    continue
                print("  %s = %r" % (k, v))
            print()
            print("=== URL 完整 ===")
            print(" ", url)
            print()
            body = obj.get("request_body")
            print("=== request_body ===")
            if body:
                try:
                    j = json.loads(body)
                    print(json.dumps(j, ensure_ascii=False, indent=2)[:3000])
                except Exception:
                    print(repr(body)[:3000])
            else:
                print("  (空)")
            break
