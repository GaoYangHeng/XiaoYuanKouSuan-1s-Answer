# -*- coding: utf-8 -*-
# 诊断实验：随机数/时间/JNI 调用对 sign 的影响，一次跑完
# 实验1 baseline(time=TS,LCG) 2/3 seed固定 4 rand恒0 5 time偏移
# 同时 dump：time/srand/rand 序列、JNI 调用序列、每轮 MD5 输入（定位 rand 出现位置）
import sys, io, hashlib
from contextlib import redirect_stdout

sys.path.insert(0, r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign")
import emulator as em
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_PC, UC_ARM_REG_LR

PATH = "/leo-game-pk/android/math/pk/match/v2"
KEY = "wdi4n2t8edr"
TS = 1788059164


class Emu5(em.Emulator):
    def __init__(self, tag, seed_override=None, rand_mode="lcg", time_val=TS):
        super().__init__()
        self.tag = tag
        self.seed_override = seed_override
        self.rand_mode = rand_mode
        self.time_val = time_val
        self.calls = []

    def _handle_external(self, name):
        if name == "time":
            self.calls.append(("time",))
            self.uc.reg_write(UC_ARM_REG_R0, self.time_val)
            self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(LR))
            return
        if name == "srand":
            self.calls.append(("srand", self.uc.reg_read(UC_ARM_REG_R0)))
            if self.seed_override is not None:
                self.rand_state = self.seed_override
                self.uc.reg_write(UC_ARM_REG_R0, 0)
                self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(LR))
                return
            return super()._handle_external(name)
        if name == "rand":
            self.calls.append(("rand",))
            if self.rand_mode == "zero":
                self.uc.reg_write(UC_ARM_REG_R0, 0)
                self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(LR))
                return
            return super()._handle_external(name)
        return super()._handle_external(name)

    def _jni_hook(self, name):
        try:
            r1 = self.uc.reg_read(UC_ARM_REG_R1)
        except Exception:
            r1 = -1
        self.calls.append(("JNI_" + name, r1))
        return super()._jni_hook(name)


def run(seed_override=None, rand_mode="lcg", time_val=TS):
    buf = io.StringIO()
    e = Emu5("x", seed_override, rand_mode, time_val)
    err = ""
    with redirect_stdout(buf):
        try:
            e.start(PATH, KEY, TS)
        except Exception as ex:
            err = type(ex).__name__ + ":" + str(ex)[:80]
    final = hashlib.md5(e.md5_inputs[-1]).hexdigest() if e.md5_inputs else None
    return final, e.calls, e.md5_inputs, buf.getvalue(), err


EXPS = [
    ("实验1 baseline（time=TS，LCG rand）", dict()),
    ("实验2 srand seed=12345", dict(seed_override=12345)),
    ("实验3 srand seed=99999", dict(seed_override=99999)),
    ("实验4 rand 恒返回 0", dict(rand_mode="zero")),
    ("实验5 time=TS+100（time 是否进链）", dict(time_val=TS + 100)),
]

results = []
for title, kw in EXPS:
    f, calls, mins, out, err = run(**kw)
    results.append((title, f, calls, mins, err))
    print("=" * 78)
    print(title)
    print("  final=%s  %s" % (f, err))

print()
print("=" * 78)
print("final 对比（baseline=%s）：" % results[0][1])
for i in range(1, len(results)):
    t, f = results[i][0], results[i][1]
    mark = "  ← 变化！该因素进链" if f != results[0][1] else ""
    print("  %s = %s%s" % (t.split()[1], f, mark))

print()
print("=" * 78)
print("baseline 的 time/srand/rand 调用序列：")
for c in results[0][2]:
    if c[0] in ("time", "srand", "rand"):
        print("  %s" % (c,))
print()
print("baseline 的 JNI 调用序列（按序）：")
for c in results[0][2]:
    if c[0].startswith("JNI_"):
        print("  %s" % (c,))

print()
print("=" * 78)
print("baseline 每轮 MD5 输入（长度 / 可打印段 / 十六进制头 96B）：")
for i, m in enumerate(results[0][3]):
    b = m if isinstance(m, bytes) else str(m).encode("utf-8", "replace")
    printable = "".join(chr(x) if 32 <= x < 127 else "." for x in b[:200])
    print("  轮%d len=%d" % (i + 1, len(b)))
    print("    前200可打印: %s" % printable)
    if len(b) > 200:
        print("    尾48B hex: %s" % b[-48:].hex())

with open(r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\trace_baseline.txt", "w", encoding="utf-8") as f:
    f.write(results[0][4])
print()
print("完整 trace 已存 trace_baseline.txt")
