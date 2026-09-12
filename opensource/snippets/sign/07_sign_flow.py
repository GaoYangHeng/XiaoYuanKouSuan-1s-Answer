# 片段：用 Unicorn 模拟执行官方 .so 生成真实签名（调用骨架）
# 说明：签名的 T410 段是 410 字节的时间戳编码流，无法用纯 Python 逆出闭式解，
#       可靠做法是直接让 Unicorn 跑官方 .so。
# 已脱敏：仅展示调用骨架，不含模拟器实现（见 emulator.py 思路）。

import importlib.util


def load_emulator(emulator_py):
    spec = importlib.util.spec_from_file_location("emulator", emulator_py)
    em = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(em)
    return em


def real_sign(em, path, ts_sec):
    """path: 待签名的路径（原样传入）；ts_sec: 秒级时间戳"""
    e = em.Emulator()
    e.time_ret = ts_sec                      # 固定模拟器的时间返回值
    e.start(path, "wdi4n2t8edr", ts_sec)     # (path, key, ts)
    return e.final_sign


def build_url(host, path, sign, extra=""):
    q = ("_productId=611&platform=android34&version=3.141.1&vendor=tencent"
         "&deviceCategory=phone&av=5&webviewVersion=131&whRatio=2.06"
         "&isBackground=0&sign=" + sign)
    if extra:
        q = extra + "&" + q
    return host + path + "?" + q


"""
签名算法（官方真机 5/5 命中）
------------------------------------------------------------------
K     = "wdi4n2t8edr"
P     = path 原样
h1    = md5(P + K)
h2    = md5(P + K + h1 + P)
h3    = md5(P + K + h1 + P + h2 + T410)
final = md5(P + K + h1 + P + h2 + T410 + h3 + K)

T410 = f(ts)：由 .so 偏移 0x44280 的编码器产出，410 字节的 %lu 十进制拼接流，
             只依赖时间戳。

调用链：
   ds.c5.c().b(path)
     -> e.zcvsd1wr2t(str, key, ts)
     -> libRequestEncoder.so（主 JNI 函数 VA 0x414E8）

注意事项
------------------------------------------------------------------
- 仓库中若存在把 T410 简化成 str(ts // 60) 的参考实现，那是从未真机验证的简化式，
  与上述权威结论不一致，不可直接用于生产。
- PC 侧实验：读接口（history / home）可用；写接口（match 系列）始终 417，
  即便复刻完整 WebView header 也无效，推测缺 SDK 设备指纹。
"""
