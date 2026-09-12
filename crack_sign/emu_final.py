# -*- coding: utf-8 -*-
# 一次性决定性枚举：模拟器 × stub 候选 × T 变体，自动对比 Test 真机 3 样本
# 全部组合一次跑完，不依赖外部交互
import sys, io, hashlib
from contextlib import redirect_stdout

sys.path.insert(0, r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign")
import emulator as em

PATH = "/leo-game-pk/android/math/pk/match/v2"
KEY = "wdi4n2t8edr"
CRACK = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign"

TEST_SAMPLES = [
    (1788059164, "c09aca9582fbe0a788022afbcba3e4af"),
    (1788059228, "95b23547d8c598bc3df4f484620abb49"),
    (1788059354, "a8a69657806a8e639a9c0832225bb405"),
]
FENBI_SAMPLE = (1788084659, "d9a0ede59cd64436379a3d6e716c3f74")

CERT_MD5 = "da8e2ec9722dee7ab20752a92e588667"
CERT_SHA256 = "cae28ac067e030162deac0a65394717a6d89066d906f80631eb800ae3d16c8bf"
CERT_MD5_HEXSTR = "3779f66ceb0767431ab9c507679fba98"
AID = "39c0141952095d9c"
AID_MD5 = hashlib.md5(AID.encode()).hexdigest()
SDK = "34"

TEST_CERT_HEX = open(CRACK + r"\test_cert_hex.txt", encoding="utf-8").read().strip()
FENBI_CERT_HEX = open(CRACK + r"\device_id.txt", encoding="utf-8").read().strip()

STUBS = [
    ("Test_DERhex", TEST_CERT_HEX.encode()),
    ("CERT_MD5", CERT_MD5.encode()),
    ("CERT_MD5_HEXSTR", CERT_MD5_HEXSTR.encode()),
    ("CERT_SHA256", CERT_SHA256.encode()),
    ("AID", AID.encode()),
    ("AID_MD5", AID_MD5.encode()),
    ("SDK", SDK.encode()),
    ("empty", b""),
    ("FAKE", b"TEST_DEVICE_ID_FAKE"),
]


class Emu2(em.Emulator):
    def __init__(self, stub, time_val):
        super().__init__()
        self.time_val = time_val
        self.stub_ret = stub

    def _handle_external(self, name):
        if name == "time":
            self.uc.reg_write(em.UC_ARM_REG_R0, self.time_val)
            self.uc.reg_write(em.UC_ARM_REG_PC, self.uc.reg_read(em.UC_ARM_REG_LR))
            return
        return super()._handle_external(name)


def run_once(stub, ts):
    buf = io.StringIO()
    e = Emu2(stub, ts)
    err = ""
    with redirect_stdout(buf):
        try:
            e.start(PATH, KEY, ts)
        except Exception as ex:
            err = type(ex).__name__ + ":" + str(ex)[:80]
    out = buf.getvalue()
    delta = ""
    for line in out.splitlines():
        if line.startswith("[delta]"):
            delta = line
    final = hashlib.md5(e.md5_inputs[-1]).hexdigest() if e.md5_inputs else None
    return final, len(e.md5_inputs), delta, err, out, e.md5_inputs


print("=" * 72)
print("阶段1：Test 样本1 全枚举（9 stub × T-1/T/T+1）")
ts0, sig0 = TEST_SAMPLES[0]
hits = []
for name, stub in STUBS:
    for dt in (0, -60, 60):
        tv = ts0 + dt
        final, n, delta, err, out, inputs = run_once(stub, tv)
        tag = "HIT!!!" if final == sig0 else "miss"
        print("[样本1] stub=%-15s tv=%d T=%d 轮数=%d final=%s %s %s | %s" % (
            name, tv, tv // 60, n, final, tag, err, delta[:60]))
        if final == sig0:
            hits.append((name, stub))
        if name == "Test_DERhex" and dt == 0:
            print("  --- Test_DERhex/T0 的 MD5 链 ---")
            for i, d in enumerate(inputs, 1):
                print("   轮%d(%dB): %s" % (i, len(d), d[:80]))
print()
print("=" * 72)
print("阶段2：命中的 stub 验证 Test 全部 3 条")
for name, stub in hits:
    okc = 0
    for ts, sig in TEST_SAMPLES:
        final, n, delta, err, out, inputs = run_once(stub, ts)
        ok = final == sig
        okc += 1 if ok else 0
        print("[验证] stub=%-15s ts=%d final=%s 真机=%s %s" % (
            name, ts, final, sig, "HIT" if ok else "MISS"))
    print("==> stub=%s 命中 %d/3 %s" % (name, okc, "### 完全确定 ###" if okc == 3 else ""))
if not hits:
    print("(阶段1 无命中)")
print()
print("=" * 72)
print("阶段3：FENBI 对照（DERhex × T-1/T/T+1）")
tsf, sigf = FENBI_SAMPLE
for dt in (0, -60, 60):
    tv = tsf + dt
    final, n, delta, err, out, inputs = run_once(FENBI_CERT_HEX.encode(), tv)
    print("[FENBI] tv=%d T=%d 轮数=%d final=%s %s %s | %s" % (
        tv, tv // 60, n, final, "HIT!!!" if final == sigf else "miss", err, delta[:60]))
print()
print("全部枚举结束")
