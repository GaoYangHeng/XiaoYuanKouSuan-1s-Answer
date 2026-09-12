# 环境差异矩阵：一次跑完 真机 vs 模拟器 全部环境差异假设，对照 signprobe 真机 sign
# 差异源：SDK_INT(0x258)、CallStaticObjectMethod 返回对象(0x1c8)、memcmp 返回值语义
import io
import hashlib
import contextlib
import emulator as em

BASE_DIR = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign"
PATH = "/leo-game-pk/android/math/pk/match/v2"
KEY = "wdi4n2t8edr"
TS = 1788059164
PKG = b"com.fenbi.android.leo"
HEX1 = bytes.fromhex("1dcd877d86d19882d8d055a1a87de93c")

with open(BASE_DIR + r"\test_cert_hex.txt") as f:
    STUB_TEST = f.read().strip()

# 真机 memcmp 语义：返回首差异字节的 (unsigned char) 差值
MD5_TEST = hashlib.md5(STUB_TEST.encode()).digest()
DIFF_I = next(i for i in range(16) if MD5_TEST[i] != HEX1[i])
DEV_VAL = MD5_TEST[DIFF_I] - HEX1[DIFF_I]

TRUTH = {
    "c09aca9582fbe0a788022afbcba3e4af": "真机@1788059164",
    "95b23547d8c598bc3df4f484620abb49": "真机@1788059228",
    "a8a69657806a8e639a9c0832225bb405": "真机@1788059354",
    "789f847243914a787764055f39972f4d": "模拟器base",
}

CFGS = [
    ("base", {}),
    ("SDK34", dict(sdk_ret=34)),
    ("pkg", dict(static_obj_bytes=PKG)),
    ("SDK34+pkg", dict(sdk_ret=34, static_obj_bytes=PKG)),
    ("memcmp=0", dict(memcmp_force=0)),
    ("memcmp=+1", dict(memcmp_force=1)),
    ("memcmp=dev%+d" % DEV_VAL, dict(memcmp_force=DEV_VAL)),
    ("memcmp=-dev%+d" % DEV_VAL, dict(memcmp_force=-DEV_VAL)),
    ("SDK34+pkg+memcmp0", dict(sdk_ret=34, static_obj_bytes=PKG, memcmp_force=0)),
    ("SDK34+pkg+memcmpdev", dict(sdk_ret=34, static_obj_bytes=PKG, memcmp_force=DEV_VAL)),
]


class MatrixEmu(em.Emulator):
    def __init__(self, cfg):
        super().__init__()
        self.stub_ret = STUB_TEST.encode()
        self.sdk_ret = cfg.get("sdk_ret")
        self.memcmp_force = cfg.get("memcmp_force")
        self.static_obj_bytes = cfg.get("static_obj_bytes")
        self.jni_calls = []
        self.ext_calls = {}

    def _jni_hook(self, name):
        self.jni_calls.append(name)
        return super()._jni_hook(name)

    def _handle_external(self, name):
        self.ext_calls[name] = self.ext_calls.get(name, 0) + 1
        return super()._handle_external(name)


print(f"md5(test_cert) 首差异偏移={DIFF_I}  设备memcmp返回值={DEV_VAL}")
print("=" * 90)

for label, cfg in CFGS:
    e = MatrixEmu(cfg)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            e.start(PATH, KEY, TS)
    except Exception as ex:
        print(f"[{label}] 异常: {ex}")
        continue
    out = buf.getvalue()
    deltas = [ln for ln in out.splitlines() if "[delta]" in ln]
    sign = e.final_sign
    lens = [len(x) for x in e.md5_inputs]
    unks = sorted(set(c for c in e.jni_calls if c.startswith("unk_")))
    hit = TRUTH.get(sign or "", "未命中")
    print(f"[{label}] final={sign}")
    print(f"    轮长={lens}  命中: {hit}  JNI数={len(e.jni_calls)}  未知偏移={unks}")
    for d in deltas[:2]:
        print(f"    {d}")

print("=" * 90)
print("全部配置跑完")
