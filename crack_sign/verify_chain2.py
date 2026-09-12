# -*- coding: utf-8 -*-
# 验证 5 个 MD5 调用之间的链式关系与 X 字段身份
import hashlib, re

LOG = "run_real44280_10.log"

def md5h(b):
    return hashlib.md5(b).hexdigest()

def main():
    raw = open(LOG, "rb").read().decode("utf-8", "replace")
    # 每次真实 MD5 调用打印一行 "[MD5] hex: <输入数据的hex>"，用它可靠还原字节
    hexlines = re.findall(r"\[MD5\] hex: ([0-9a-f]+)", raw)
    ins = [bytes.fromhex(h) for h in hexlines]
    print(f"提取到 {len(ins)} 个 MD5 输入")
    if len(ins) < 5:
        return
    cert, in2, in3, in4, in5 = ins[0], ins[1], ins[2], ins[3], ins[4]
    P = b".solar-activity/android/activity/6"  # P'（delta 已应用后的路径）
    K = b"wdi4n2t8edr"
    print(f"证书hex({len(cert)}B) 头32: {cert[:32].decode()} 尾16: {cert[-16:].decode()}")

    hc = md5h(cert)  # = md5(证书hex字符串的ASCII字节)，即日志第1个digest 1dcd877d...
    h1 = md5h(in2)
    h2 = md5h(in3)
    h3 = md5h(in4)
    fin = md5h(in5)
    print(f"hc=md5(certHexASCII) = {hc}")
    print(f"h1 = {h1}")
    print(f"h2 = {h2}")
    print(f"h3 = {h3}")
    print(f"final=md5(in5)      = {fin}")

    # 结构验证
    ok = []
    ok.append(("in2 = P'+K", in2 == P + K))
    ok.append(("in3 = P'+K+h1+P'", in3 == P + K + h1.encode() + P))
    # in4 = P'+K+h1+P'+h2+T → 去公共前缀后是 h2+T
    h2t = in4[len(in3):]
    T = h2t[32:]
    ok.append(("in4 去前缀 == h2+T", h2t == h2.encode() + T))
    print(f"T({len(T)}B) 头20: {T[:20].decode()}")

    # in5 = P'+K+h1+P'+h2+T+X+K → 去公共前缀后是 h2+T+X+K
    tail = in5[len(in3):]
    ok.append(("in5 去前缀 以 h2 开头", tail.startswith(h2.encode())))
    rest = tail[32:]
    ok.append(("in5 追加部分以 T 开头", rest.startswith(T)))
    if rest.startswith(T):
        after = rest[len(T):]
        X2 = after[: len(after) - len(K)] if after.endswith(K) else after
        X = X2.decode()
        print(f"X(32字符) = {X}")
        # X 身份候选
        cands = {
            "hc = md5(证书hex ASCII 字节)": hc,
            "md5(证书 DER 原始字节)": md5h(bytes.fromhex(cert.decode())),
            "h3": h3,
            "h1": h1,
            "h2": h2,
        }
        for name, v in cands.items():
            ok.append((f"X == {name}", X == v))
        if not any(X == v for v in cands.values()):
            print("X 不等于任何已知候选 → 可能有未被 hook 的第 6 处哈希或 Java 层来源")
    for name, v in ok:
        print(f"  [{'OK ' if v else 'FAIL'}] {name}")

if __name__ == "__main__":
    main()
