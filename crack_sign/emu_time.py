# -*- coding: utf-8 -*-
# 决定性实验：native 的 T 来自 time(NULL) 还是传入 ts 参数？
# 解耦两者：param_ts 走 JNI 栈，time() hook 单独控制
# 若 T=time()//60：用样本 ts 作 time() 值应命中真机 sign
import sys, hashlib
from contextlib import redirect_stdout
import io

sys.path.insert(0, r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign")
import emulator as em

PATH = "/leo-game-pk/android/math/pk/match/v2"
KEY = "wdi4n2t8edr"

SAMPLES = [
    ("Test1", 1788059164, "c09aca9582fbe0a788022afbcba3e4af"),
    ("Test2", 1788059228, "95b23547d8c598bc3df4f484620abb49"),
    ("Test3", 1788059354, "a8a69657806a8e639a9c0832225bb405"),
    ("FENBI", 1788084659, "d9a0ede59cd64436379a3d6e716c3f74"),
]


class Emu4(em.Emulator):
    def __init__(self, param_ts, time_val):
        super().__init__()
        self.time_val = time_val

    def _handle_external(self, name):
        if name == "time":
            self.uc.reg_write(em.UC_ARM_REG_R0, self.time_val)
            self.uc.reg_write(em.UC_ARM_REG_PC, self.uc.reg_read(em.UC_ARM_REG_LR))
            return
        return super()._handle_external(name)


def run(param_ts, time_val):
    buf = io.StringIO()
    e = Emu4(param_ts, time_val)
    err = ""
    with redirect_stdout(buf):
        try:
            e.start(PATH, KEY, param_ts)
        except Exception as ex:
            err = type(ex).__name__ + ":" + str(ex)[:60]
    final = hashlib.md5(e.md5_inputs[-1]).hexdigest() if e.md5_inputs else None
    # 提取 T（轮4 输入中 h2 之后的 8 字节：位置 37+11+32+37+32 = 149..157）
    t_str = ""
    if len(e.md5_inputs) >= 4:
        d = bytes(e.md5_inputs[3])
        t_str = d[149:157].decode(errors="replace")
    return final, t_str, err


print("=" * 78)
print("阶段1：判定 T 来源（param_ts 与 time() 解耦）")
fa, ta, _ = run(1788059164, 1788059164)
fb, tb, _ = run(1788059164, 1788059228)
fc, tc, _ = run(0, 1788059164)
print("param=1788059164 time=1788059164 -> final=%s T='%s'" % (fa, ta))
print("param=1788059164 time=1788059228 -> final=%s T='%s'" % (fb, tb))
print("param=0           time=1788059164 -> final=%s T='%s'" % (fc, tc))
if fa != fb:
    print("==> final 随 time() 变化：T 来自 time(NULL)！")
else:
    print("==> final 不随 time() 变化：T 来自参数")
if fa == fc:
    print("==> param_ts 完全无关！sign = f(path, key, time())")
print()

print("=" * 78)
print("阶段2：以 time()=样本ts、param=0 跑 4 样本 × dt{-60,0,+60}")
total_hit = 0
for name, ts, sig in SAMPLES:
    hit = False
    for dt in (0, -60, 60):
        tv = ts + dt
        final, t_str, err = run(0, tv)
        mark = "HIT!!!" if final == sig else "miss"
        print("[%s] time=%d T='%s' final=%s %s %s (真机=%s)" % (name, tv, t_str, final, mark, err, sig))
        if final == sig:
            hit = True
            total_hit += 1
    print("-" * 60)
print("命中数：%d" % total_hit)
print("全部结束")
