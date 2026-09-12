import zipfile
import hashlib

apk = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\testapp\base.apk"
z = zipfile.ZipFile(apk)
names = [n for n in z.namelist() if n.startswith("META-INF/")]
print("META-INF 内容:", names)

# 找证书文件
cert_names = [n for n in names if n.endswith((".RSA", ".DSA", ".EC"))]
for cn in cert_names:
    data = z.read(cn)
    print(f"\n证书文件: {cn} ({len(data)} 字节)")
    # 提取 DER 证书（PKCS7 里的第一个证书）
    # 简单方法：直接对整个 PKCS7 算 hex（Signature 用的是 cert.getEncoded()，即单个证书 DER，不是 PKCS7）
    print("PKCS7 前 64 字节 hex:", data[:64].hex())
    print("PKCS7 MD5:", hashlib.md5(data).hexdigest())
    print("PKCS7 SHA1:", hashlib.sha1(data).hexdigest())

# 尝试用 cryptography 解析证书
try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.serialization import pkcs7
    for cn in cert_names:
        data = z.read(cn)
        # 尝试直接加载证书（如果是裸证书）
        try:
            cert = x509.load_der_x509_certificate(data)
            der = cert.public_bytes(serialization.Encoding.DER)
            print(f"\n[{cn}] 是裸 DER 证书")
            print("证书 DER hex (前100):", der.hex()[:100])
            print("证书 DER 长度:", len(der))
            print("证书 DER MD5:", hashlib.md5(der).hexdigest())
            print("证书 DER SHA1:", hashlib.sha1(der).hexdigest())
        except Exception as e:
            print(f"\n[{cn}] 不是裸证书: {e}")
            # 尝试 PKCS7
            try:
                certs = pkcs7.load_der_pkcs7_certificates(data)
                for i, cert in enumerate(certs):
                    der = cert.public_bytes(serialization.Encoding.DER)
                    print(f"PKCS7 证书[{i}] DER 长度: {len(der)}")
                    print(f"  DER hex (前80): {der.hex()[:80]}")
                    print(f"  DER MD5: {hashlib.md5(der).hexdigest()}")
                    print(f"  DER SHA1: {hashlib.sha1(der).hexdigest()}")
            except Exception as e2:
                print(f"  PKCS7 也失败: {e2}")
except ImportError:
    print("cryptography 未安装，仅输出原始 hex")
