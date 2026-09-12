# NOTE: the capture/sample data this script depends on was removed from the repo. Kept for archive/reference only.
import json, base64, os

P = r"f:\traework_main workspace\xiaoyuan-kousuan-re\capture\pk_traffic.jsonl"
OUT = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\samples"

os.makedirs(OUT, exist_ok=True)

rows = []
with open(P, "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue

seen = 0
for i, obj in enumerate(rows):
    url = obj.get("url") or ""
    if not (isinstance(url, str) and "match/v2" in url):
        continue
    body = obj.get("body") or ""
    if not isinstance(body, str) or not body.startswith("base64:"):
        continue
    b64 = body[len("base64:"):]
    try:
        raw = base64.b64decode(b64)
    except Exception as e:
        print(f"[{i}] base64 解码失败: {e}")
        continue
    seen += 1
    fn = os.path.join(OUT, f"match_{i}.bin")
    with open(fn, "wb") as f:
        f.write(raw)
    print(f"[{i}] {len(raw)} 字节 -> {fn}")
    print(f"   hex_head={raw[:24].hex()}")
    # 提取 URL 里的时间戳/sign 便于关联
    print(f"   url={url[:100]}")

print(f"\n共解码 {seen} 个 match/v2 响应体，保存到 {OUT}")
