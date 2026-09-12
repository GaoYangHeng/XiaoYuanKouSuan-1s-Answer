# -*- coding: utf-8 -*-
# 全量 JNI dump：一次运行拿到 native 对环境的全部提问（类/方法/字段/参数/memcmp 数据）
import io, contextlib
import emulator as em

BASE_DIR = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign"
PATH = "/leo-game-pk/android/math/pk/match/v2"
KEY = "wdi4n2t8edr"
TS = 1788059164

e = em.Emulator()  # 官方证书 stub
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    e.start(PATH, KEY, TS)
log = buf.getvalue()

with open(BASE_DIR + r"\dump_full.log", "w", encoding="utf-8") as f:
    f.write(log)

print(f"final_sign = {e.final_sign}")
print(f"真机       = c09aca9582fbe0a788022afbcba3e4af")
print(f"输出已存 dump_full.log（{len(log)} 字符）")
print("=" * 60)
# 只打印 JNI 交互摘要行（不含 trace）
for line in log.splitlines():
    if line.startswith("[trace]"):
        continue
    if line.startswith("[HOOK]") and ("JNI" not in line):
        continue
    print(line)
