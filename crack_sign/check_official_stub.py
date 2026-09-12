# -*- coding: utf-8 -*-
# 最高优先级验证：官方证书 stub @ 真机同参数，对比真机 sign c09aca95...
import io, contextlib
import emulator as em

BASE_DIR = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign"
PATH = "/leo-game-pk/android/math/pk/match/v2"
KEY = "wdi4n2t8edr"
TS = 1788059164
TRUTH = "c09aca9582fbe0a788022afbcba3e4af"

with open(BASE_DIR + r"\device_id.txt") as f:
    official = f.read().strip()
print(f"官方证书 stub 长度: {len(official)}")

e = em.Emulator()  # stub_ret 默认从 device_id.txt 读 = 官方证书
assert e.stub_ret.decode() == official, "stub_ret 不是官方证书"
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    e.start(PATH, KEY, TS)
log = buf.getvalue()
print("=" * 60)
print(f"官方证书 stub @ (path, K, {TS})")
print(f"  模拟器 final_sign = {e.final_sign}")
print(f"  真机 signprobe    = {TRUTH}")
print(f"  命中: {e.final_sign == TRUTH}")
# 轮次信息
for line in log.splitlines():
    if "44280" in line or "delta" in line or "MD5] 输入(" in line and len(line) < 120:
        pass
print(f"  MD5 调用数: {len(e.md5_inputs)}")
for i, d in enumerate(e.md5_inputs):
    head = d[:48]
    print(f"  md5[{i}] len={len(d)} head={head!r}")
