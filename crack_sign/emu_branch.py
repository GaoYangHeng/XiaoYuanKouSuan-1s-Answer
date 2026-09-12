# -*- coding: utf-8 -*-
# 一次性分支实验：dump memcmp 两边内容 + 强制 memcmp==0 走相等分支
# 验证假设：模拟器与真机差异来自 memcmp 校验分支（h1 选择）
# 全部变体一次跑完，纯离线零手机操作
import sys, io, hashlib
from contextlib import redirect_stdout

sys.path.insert(0, r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign")
import emulator as em

PATH = "/leo-game-pk/android/math/pk/match/v2"
KEY = "wdi4n2t8edr"
TS = 1788059164
HEX1 = open(r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\hex1.txt").read().strip()

# 三个候选真机 sign（同 ts 不同来源）
TARGETS = {
    "Test_crack_sig_pos": "c09aca9582fbe0a788022afbcba3e4af",
    "hex1样本": "7ccaf869bade9bf18c8f0c3e8a034e23",
    "FENBI": "d9a0ede59cd64436379a3d6e716c3f74",
}

TEST_CERT_HEX = open(r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\device_id.txt").read().strip()


class Emu3(em.Emulator):
    def __init__(self, stub, time_val, mode="normal"):
        super().__init__()
        self.time_val = time_val
        self.stub_ret = stub
        self.mode = mode
        self.memcmp_log = []

    def _handle_external(self, name):
        if name == "time":
            self.uc.reg_write(em.UC_ARM_REG_R0, self.time_val)
            self.uc.reg_write(em.UC_ARM_REG_PC, self.uc.reg_read(em.UC_ARM_REG_LR))
            return
        if name == "memcmp":
            uc = self.uc
            r0 = uc.reg_read(em.UC_ARM_REG_R0)
            r1 = uc.reg_read(em.UC_ARM_REG_R1)
            r2 = uc.reg_read(em.UC_ARM_REG_R2)
            a = bytes(uc.mem_read(r0, r2))
            b = bytes(uc.mem_read(r1, r2))
            ret = 0 if a == b else (1 if a > b else -1)
            if self.mode == "force0_all":
                ret = 0
            elif self.mode == "force0_32" and r2 == 32:
                ret = 0
            elif self.mode == "force0_16" and r2 == 16:
                ret = 0
            self.memcmp_log.append({"len": r2, "a": a, "b": b, "ret": ret})
            uc.reg_write(em.UC_ARM_REG_R0, ret & 0xFFFFFFFF)
            uc.reg_write(em.UC_ARM_REG_PC, uc.reg_read(em.UC_ARM_REG_LR))
            return
        return super()._handle_external(name)


def run_once(stub, tv, mode):
    buf = io.StringIO()
    e = Emu3(stub, tv, mode)
    err = ""
    with redirect_stdout(buf):
        try:
            e.start(PATH, KEY, tv)
        except Exception as ex:
            err = type(ex).__name__ + ":" + str(ex)[:60]
    final = hashlib.md5(e.md5_inputs[-1]).hexdigest() if e.md5_inputs else None
    h1 = e.md5_inputs[2][48:80] if len(e.md5_inputs) >= 3 else b""
    delta = ""
    for line in buf.getvalue().splitlines():
        if line.startswith("[delta]"):
            delta = line
    return final, h1, e.memcmp_log, delta, err, e.md5_inputs


VARIANTS = [
    ("baseline", TEST_CERT_HEX.encode(), "normal"),
    ("force0_all", TEST_CERT_HEX.encode(), "force0_all"),
    ("force0_32", TEST_CERT_HEX.encode(), "force0_32"),
    ("force0_16", TEST_CERT_HEX.encode(), "force0_16"),
    ("stub_hex1", HEX1.encode(), "normal"),
    ("stub_hex1+force0_32", HEX1.encode(), "force0_32"),
    ("stub_empty+force0_all", b"", "force0_all"),
]

print("hex1 =", HEX1)
print("=" * 78)
results = {}
for name, stub, mode in VARIANTS:
    final, h1, mlog, delta, err, inputs = run_once(stub, TS, mode)
    results[name] = (final, h1, mlog)
    hit = [tn for tn, ts_ in TARGETS.items() if ts_ == final]
    print("[%s] final=%s %s 轮数=%d %s" % (name, final, ("HIT:" + ",".join(hit)) if hit else "miss", len(inputs), err))
    print("   h1(轮3输入[48:80]) = %s  %s" % (h1.decode(errors="replace"), "★h1==hex1" if h1.decode(errors="replace") == HEX1 else ""))
    print("   %s" % delta[:80])
    for i, m in enumerate(mlog):
        print("   memcmp#%d len=%d ret=%d" % (i, m["len"], m["ret"]))
        print("     A: %s" % m["a"][:48].hex())
        print("     B: %s" % m["b"][:48].hex())
        print("     A_ascii: %r" % m["a"][:48])
        print("     B_ascii: %r" % m["b"][:48])
    print("-" * 78)

print()
print("MD5 链（baseline 轮次输入前 100 字节）:")
final, h1, mlog, delta, err, inputs = run_once(TEST_CERT_HEX.encode(), TS, "normal")
for i, d in enumerate(inputs, 1):
    print("  轮%d(%dB): %s" % (i, len(d), d[:100]))
print()
print("全部变体结束")
