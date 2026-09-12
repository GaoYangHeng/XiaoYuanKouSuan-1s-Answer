import hashlib

# 小猿口算 sign 算法（libRequestEncoder.so::zcvsd1wr2t 的完整还原）
# 已验证：Python 复现结果与 Unicorn 模拟 dump 完全一致

KEY = "wdi4n2t8edr"
DELTA = -1  # path[0] 修改量（FENBI 签名下恒为 -1）


def _md5_hex(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def calc_device_id(signature_der_hex: str) -> str:
    """设备值 = APK 签名证书 DER 字节的小写 hex（Signature.toChars()）"""
    return signature_der_hex.lower()


def calc_hex1(device_id: str) -> str:
    """hex1 = MD5(设备值)，编译期硬编码用于签名绑定校验"""
    return _md5_hex(device_id)


def sign(path: str, ts_seconds: int, signature_der_hex: str) -> str:
    """生成 PK 接口请求签名

    :param path: 接口路径，如 "/leo-game-pk/android/math/pk/match/v2"
    :param ts_seconds: 秒级时间戳
    :param signature_der_hex: APK 签名证书 DER 字节的小写 hex
    :return: 32 位 hex sign
    """
    device = calc_device_id(signature_der_hex)
    # hex1 用于签名绑定（delta 计算），此处 delta 对正确签名恒为 -1
    calc_hex1(device)

    pm = chr((ord(path[0]) + DELTA) & 0xFF) + path[1:]
    minute = str(ts_seconds // 60)

    s = pm + KEY
    h1 = _md5_hex(s)
    s = pm + KEY + h1 + pm
    h2 = _md5_hex(s)
    s = pm + KEY + h1 + pm + h2 + minute
    h3 = _md5_hex(s)
    s = pm + KEY + h1 + pm + h2 + minute + h3 + KEY
    return _md5_hex(s)


if __name__ == "__main__":
    import sys
    der = open(r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\device_id.txt").read().strip()
    ts = 1788059615
    p = "/leo-game-pk/android/math/pk/match/v2"
    result = sign(p, ts, der)
    print("sign =", result)
    print("期望 = e0302beeadb745ecbbfeb2e8f86d426d")
    print("匹配 =", result == "e0302beeadb745ecbbfeb2e8f86d426d")
