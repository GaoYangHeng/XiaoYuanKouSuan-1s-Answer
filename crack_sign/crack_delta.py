# -*- coding: utf-8 -*-
# delta 全域爆破：path[0] 修改量 d ∈ [-256, 256]，分别对 组3(测试签名probe) 和 组1(官方真机流量) 求全命中
# 依据：dump_full.log 实测 delta c=-1 对应 (结果1=1, 结果2=0)，假设 delta = f(结果1, 结果2)
# 测试签名下 结果2=-1 → delta 预测 = -2
import hashlib

KEY = "wdi4n2t8edr"
PATH = "/leo-game-pk/android/math/pk/match/v2"

def md5s(s):
    return hashlib.md5(s.encode()).hexdigest()

def make_sign(p, ts, d):
    pm = chr((ord(p[0]) + d) & 0xFF) + p[1:]
    T = str(ts // 60)
    h1 = md5s(pm + KEY)
    h2 = md5s(pm + KEY + h1 + pm)
    h3 = md5s(pm + KEY + h1 + pm + h2 + T)
    return md5s(pm + KEY + h1 + pm + h2 + T + h3 + KEY)

g3 = [(1788059164, "c09aca9582fbe0a788022afbcba3e4af"),
      (1788059228, "95b23547d8c598bc3df4f484620abb49"),
      (1788059354, "a8a69657806a8e639a9c0832225bb405")]
g1 = [(1788084659, "d9a0ede59cd64436379a3d6e716c3f74"),
      (1788084681, "4d4fb91c395b601b9b61816f16420484"),
      (1788084809, "57e40701ec58b4d9c89f471310ad3270"),
      (1788084859, "296bca5eaca63108fd727d1035173222"),
      (1788085018, "03f6ab5174f50e90bce5645947bf11e6")]

for label, group in (("组3 Test签名probe", g3), ("组1 官方真机流量", g1)):
    allhits = [d for d in range(-256, 257)
               if all(make_sign(PATH, ts, d) == sig for ts, sig in group)]
    print("%s delta 全命中: %s" % (label, allhits if allhits else "无"))
    for ts, sig in group:
        per = [d for d in range(-256, 257) if make_sign(PATH, ts, d) == sig]
        if per:
            print("  单样本 ts=%d sig=%s.. -> delta=%s" % (ts, sig[:8], per))

# 第二阶段：组3 的 T 变体 × delta ∈ {-2,-1,0,1}（若第一阶段无命中）
print("\n=== 组3 T 变体扫描 ===")
def t_variants(ts):
    return {
        "ts//60": str(ts // 60),
        "ts": str(ts),
        "ts*1000//60": str(ts * 1000 // 60),
        "hex8": "%08x" % (ts & 0xFFFFFFFF),
        "HEX8": "%08X" % (ts & 0xFFFFFFFF),
        "ts%86400//60": str(ts % 86400 // 60),
        "ts+28800//60": str((ts + 28800) // 60),
        "ts-28800//60": str((ts - 28800) // 60),
    }
tnames = list(t_variants(0).keys())
for d in (-2, -1, 0, 1):
    for tn in tnames:
        ok = 0
        for ts, sig in g3:
            tv = t_variants(ts)[tn]
            pm = chr((ord(PATH[0]) + d) & 0xFF) + PATH[1:]
            h1 = md5s(pm + KEY)
            h2 = md5s(pm + KEY + h1 + pm)
            h3 = md5s(pm + KEY + h1 + pm + h2 + tv)
            got = md5s(pm + KEY + h1 + pm + h2 + tv + h3 + KEY)
            if got == sig:
                ok += 1
        if ok:
            print("  delta=%d T=%s -> %d/3" % (d, tn, ok))
print("扫描完成")
