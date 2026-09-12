import sys
sys.path.insert(0, r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign")
from emulator import Emulator

PATH = "/leo-game-pk/android/math/pk/match/v2"
KEY = "wdi4n2t8edr"
BASE = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign"

TARGETS = {
    "c09aca9582fbe0a788022afbcba3e4af": "组3 Test签名真机 @1788059164",
    "d9a0ede59cd64436379a3d6e716c3f74": "组1 FENBI官方真机 @1788084659",
}

def run(tag, cert_hex, ts):
    print(f"\n{'='*20} {tag} ts={ts} {'='*20}")
    e = Emulator()
    if cert_hex:
        e.stub_ret = cert_hex.encode()
    e.time_ret = ts
    e.start(PATH, KEY, ts)
    s = e.final_sign
    print(f"[{tag}] final_sign={s}")
    if s:
        for t, desc in TARGETS.items():
            if s == t:
                print(f"[{tag}] >>>>>>> HIT: {desc} <<<<<<<")
    return s

off = open(BASE + r"\device_id.txt").read().strip()
tst = open(BASE + r"\test_cert_hex.txt").read().strip()

run("A-OFFICIAL-9164", off, 1788059164)
run("B-TESTCERT-9164", tst, 1788059164)
run("C-OFFICIAL-4659", off, 1788084659)

print("\n真机基准：")
print("  组3: c09aca9582fbe0a788022afbcba3e4af @1788059164")
print("  组1: d9a0ede59cd64436379a3d6e716c3f74 @1788084659")
