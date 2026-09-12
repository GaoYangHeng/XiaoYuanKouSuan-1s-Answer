# -*- coding: utf-8 -*-
# 决定性对比实验：模拟器用真机样本同 ts 跑，输出 vs 真机 sign
import sys
sys.path.insert(0, r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign")
import emulator as em

PATH = "/leo-game-pk/android/math/pk/match/v2"
KEY = "wdi4n2t8edr"

class Emu2(em.Emulator):
    def __init__(self, stub_file, time_val):
        super().__init__()
        self.time_val = time_val
        self.stub_ret = open(stub_file, encoding="utf-8").read().strip().encode()

    def _handle_external(self, name):
        if name == "time":
            self.uc.reg_write(em.UC_ARM_REG_R0, self.time_val)
            self.uc.reg_write(em.UC_ARM_REG_PC, self.uc.reg_read(em.UC_ARM_REG_LR))
            return
        return super()._handle_external(name)

CRACK = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign"

# 实验 A：FENBI stub + 组1 样本1 的 ts=1788084659（真机 sign=d9a0ede59cd64436379a3d6e716c3f74）
print("=" * 60)
print("实验 A：FENBI stub ts=1788084659 真机 sign=d9a0ede5...")
e = Emu2(CRACK + r"\device_id.txt", 1788084659)
e.start(PATH, KEY, 1788084659)
print("模拟 MD5 链（最后一条输入即最终 sign 输入）:")
for i, d in enumerate(e.md5_inputs, 1):
    print("  第%d轮(%d字节): %s" % (i, len(d), d[:120] if len(d) > 120 else d))

# 实验 B：Test stub + Test 样本 ts=1788059164（真机 sign=c09aca9582fbe0a788022afbcba3e4af）
print("=" * 60)
print("实验 B：Test stub ts=1788059164 真机 sign=c09aca95...")
e2 = Emu2(CRACK + r"\test_cert_hex.txt", 1788059164)
e2.start(PATH, KEY, 1788059164)
print("模拟 MD5 链:")
for i, d in enumerate(e2.md5_inputs, 1):
    print("  第%d轮(%d字节): %s" % (i, len(d), d[:120] if len(d) > 120 else d))
