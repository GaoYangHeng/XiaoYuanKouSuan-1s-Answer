import zipfile, hashlib
from cryptography.hazmat.primitives.serialization import pkcs7, Encoding

apk = r"f:\traework_main workspace\xiaoyuan-kousuan-re\apk\com.fenbi.android.leo.apk"
z = zipfile.ZipFile(apk)
data = z.read("META-INF/FENBI.RSA")
certs = pkcs7.load_der_pkcs7_certificates(data)
cert = certs[0]
der = cert.public_bytes(Encoding.DER)
device = der.hex()  # 小写 hex = Signature.toChars()
print("设备 ID (DER hex) 长度:", len(device))
print("设备 ID 前 64:", device[:64])
print("设备 ID 后 64:", device[-64:])
hex1 = hashlib.md5(device.encode()).hexdigest()
print("\nhex1 = MD5(设备ID) =", hex1)
print("hex1 长度:", len(hex1))

# 保存设备 ID 到文件供后续使用
with open(r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\device_id.txt", "w") as f:
    f.write(device)
print("已保存 device_id.txt")

# 也保存 MD5
with open(r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\hex1.txt", "w") as f:
    f.write(hex1)
print("已保存 hex1.txt")
