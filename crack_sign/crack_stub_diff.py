# -*- coding: utf-8 -*-
# 决定性 diff：官方证书 stub vs signprobe 证书 stub（同输入 path/K/ts）
# 情形1：输出+全轮输入相同 → 证书不进链，真机差异在其他 JNI stub（generic 0 值）
# 情形2：不同 → 轮 diff 直接揭晓证书进链方式
import sys, io, contextlib
sys.path.insert(0, r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign")
from unicorn.arm_const import UC_ARM_REG_R1, UC_ARM_REG_R0, UC_ARM_REG_PC, UC_ARM_REG_LR
import emulator as em

CRACK = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign"
STUB_OFFICIAL = open(CRACK + r"\device_id.txt").read().strip().encode()
STUB_TEST = open(CRACK + r"\test_cert_hex.txt").read().strip().encode()

class DiffEmu(em.Emulator):
    def __init__(self, stub):
        super().__init__()
        self.stub_ret = stub
        self.final_sign = None
        self.jni_calls = []
        self.ext_calls = {}
    def _jni_hook(self, name):
        self.jni_calls.append(name)
        if name == "NewStringUTF":
            r1 = self.uc.reg_read(UC_ARM_REG_R1)
            s = self._read_cstr(r1)
            self.final_sign = s.decode(errors="replace")
            ret = self._make_jstring(s)
            self.uc.reg_write(UC_ARM_REG_R0, ret)
            self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(UC_ARM_REG_LR))
            return
        return super()._jni_hook(name)
    def _handle_external(self, name):
        self.ext_calls[name] = self.ext_calls.get(name, 0) + 1
        return super()._handle_external(name)

def run(stub, ts=1788059164):
    e = DiffEmu(stub)
    with contextlib.redirect_stdout(io.StringIO()):
        e.start("/leo-game-pk/android/math/pk/match/v2", "wdi4n2t8edr", ts)
    return e

a = run(STUB_OFFICIAL)
b = run(STUB_TEST)
for tag, e in (("官方证书stub", a), ("signprobe证书stub", b)):
    print(f"== {tag} ==")
    print("  final_sign:", e.final_sign)
    print("  轮长:", [len(d) for d in e.md5_inputs])
    print("  外部函数调用:", e.ext_calls)
print("== JNI 调用序列 ==")
print("官方:", ",".join(a.jni_calls))
print("Test :", ",".join(b.jni_calls))
print("== md5 轮输入逐条 diff ==")
for i in range(max(len(a.md5_inputs), len(b.md5_inputs))):
    da = a.md5_inputs[i] if i < len(a.md5_inputs) else b""
    db = b.md5_inputs[i] if i < len(b.md5_inputs) else b""
    same = da == db
    print(f"轮{i+1} len={len(da)}/{len(db)} 完全相同={same}")
    if not same:
        n = min(len(da), len(db))
        pos = next((j for j in range(n) if da[j] != db[j]), n)
        lo = max(0, pos - 16)
        print(f"  首个差异 @字节{pos}")
        print(f"  官方[{lo}:{pos+24}] = {da[lo:pos+24]!r}")
        print(f"  Test [{lo}:{pos+24}] = {db[lo:pos+24]!r}")
