# -*- coding: utf-8 -*-
# 在反编译源码中定位 c5.b(str) 调用点（确定真机传入的 str 形态）
import os, re

root = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources"
skip_marker = os.path.join("sources", "sources")

pat_call = re.compile(r'c5\b[^;\n]{0,60}?\.b\s*\(|\.b\s*\(\s*\w+\s*\)\s*;[^\n]*c5|c5\s*\.\s*c\s*\(\s*\)')
pat_import = re.compile(r'import\s+p005ds\.c5|p005ds\.c5\b')

file_hits = []
line_hits = []
for dirpath, dirs, files in os.walk(root):
    if skip_marker in dirpath:
        continue
    for fn in files:
        if not fn.endswith(".java"):
            continue
        p = os.path.join(dirpath, fn)
        try:
            t = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        has_c5 = "c5" in t
        if not has_c5:
            continue
        low = p.lower()
        if "p005ds" in low and fn == "c5.java":
            continue
        if pat_import.search(t):
            file_hits.append(p)
        for i, line in enumerate(t.splitlines(), 1):
            s = line.strip()
            if "c5" in s and ".b(" in s and len(s) < 250:
                line_hits.append("%s:%d: %s" % (p.replace(root, ""), i, s[:200]))

print("=== import/引用 p005ds.c5 的文件 ===")
for p in file_hits:
    print(p.replace(root, ""))
print()
print("=== 行级命中（含 c5 且含 .b(）===")
for h in line_hits[:100]:
    print(h)
print()
print("总计: 文件 %d, 行 %d" % (len(file_hits), len(line_hits)))
