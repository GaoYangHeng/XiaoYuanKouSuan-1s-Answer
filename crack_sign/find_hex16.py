# NOTE: the capture/sample data this script depends on was removed from the repo. Kept for archive/reference only.
import re
import glob
import json

# 从抓包文件里找所有 16 位 hex 字符串（疑似 Android ID）
files = [
    r"f:\traework_main workspace\xiaoyuan-kousuan-re\capture\pk_traffic.jsonl",
    r"f:\traework_main workspace\xiaoyuan-kousuan-re\capture\traffic.log",
]

hex16 = re.compile(r"\b[0-9a-fA-F]{16}\b")

seen = {}
for fn in files:
    try:
        with open(fn, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception as e:
        print(fn, "读取失败", e)
        continue
    for m in hex16.finditer(text):
        v = m.group(0).lower()
        seen[v] = seen.get(v, 0) + 1

print("=== 16位hex字符串（出现次数）===")
for k, v in sorted(seen.items(), key=lambda x: -x[1]):
    print(f"{k}  ×{v}")
