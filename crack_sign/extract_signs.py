# NOTE: the capture/sample data this script depends on was removed from the repo. Kept for archive/reference only.
import json
import re

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
        if "pk/match" in url:
            m = re.search(r"sign=([a-f0-9]{32})", url)
            sign = m.group(1) if m else "N/A"
            # 提取 ts 参数
            t = re.search(r"[?&]ts=(\d+)", url)
            print(f"{obj.get('ts')}  {obj.get('type')}  sign={sign}  ts={t.group(1) if t else 'N/A'}")
