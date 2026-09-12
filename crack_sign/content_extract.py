# NOTE: the capture/sample data this script depends on was removed from the repo. Kept for archive/reference only.
import json, base64

P = r"f:\traework_main workspace\xiaoyuan-kousuan-re\capture\pk_traffic.jsonl"

rows = []
with open(P, "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        rows.append(obj)

print("总记录数:", len(rows))
print("字段示例:", list(rows[0].keys()) if rows else "无")

# 找 match/v2 且有响应体的记录
for i, obj in enumerate(rows):
    # 兼容多种字段名
    url = obj.get("url") or obj.get("request", {}).get("url") or ""
    if isinstance(url, str) and "match/v2" in url:
        # 响应体可能在多个字段
        body = None
        for k in ("response_body", "resp_body", "body", "response", "content"):
            v = obj.get(k)
            if v:
                body = v
                break
        # 也可能嵌套
        if body is None:
            resp = obj.get("response") if isinstance(obj.get("response"), dict) else None
            if resp:
                body = resp.get("body") or resp.get("content")
        if body:
            print(f"\n[{i}] url={url[:80]}")
            if isinstance(body, str):
                # 可能是 base64
                try:
                    raw = base64.b64decode(body)
                    print(f"  base64 解码后 {len(raw)} 字节, hex_head={raw[:16].hex()}")
                except Exception:
                    print(f"  字符串 body 长度 {len(body)}, 前80={body[:80]!r}")
            else:
                print(f"  body 类型 {type(body)}, 值={str(body)[:80]!r}")
