# NOTE: the capture/sample data this script depends on was removed from the repo. Kept for archive/reference only.
# -*- coding: utf-8 -*-
# 提取 FENBI(原版APK) 与 Test(signprobe) 证书 DER，生成签名形态候选表 sig_forms.json
import json, zipfile, hashlib, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

APK = r"f:\traework_main workspace\xiaoyuan-kousuan-re\apk\com.fenbi.android.leo.apk"
TEST_DER = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\testapp\key_cert.der"
FENBI_OUT = r"f:\traework_main workspace\xiaoyuan-kousuan-re\fenbi_cert.der"
OUT = r"f:\traework_main workspace\xiaoyuan-kousuan-re\sig_forms.json"

# 从 PKCS#7 DER 中按 X.509 证书模式提取: SEQ{ SEQ{ tbs.. } AlgID BITSTR }
CERT_PAT = re.compile(rb"\x30\x82(..)\x30\x82(..)\xa0\x03\x02\x01\x02", re.S)

def find_cert(pkcs7: bytes):
    m = CERT_PAT.search(pkcs7)
    if not m:
        return None
    total = int.from_bytes(m.group(1), "big") + 4
    return pkcs7[m.start():m.start() + total]

with zipfile.ZipFile(APK) as z:
    blk = None
    for n in z.namelist():
        if n.upper().endswith((".RSA", ".DSA", ".EC")) and n.upper().startswith("META-INF"):
            blk = z.read(n)
            print("sig block:", n, len(blk))
            break
assert blk, "no signature block"
cert = find_cert(blk)
assert cert, "cert not found"
print("FENBI cert DER:", len(cert))

def forms(tag, der: bytes):
    h = der.hex()
    md5_d = hashlib.md5(der).hexdigest()
    sha1_d = hashlib.sha1(der).hexdigest()
    sha256_d = hashlib.sha256(der).hexdigest()
    return {
        "tag": tag,
        "der_len": len(der),
        "hex_lower": h,
        "hex_upper": h.upper(),
        "md5_of_der": md5_d,
        "md5_of_hex_lower": hashlib.md5(h.encode()).hexdigest(),
        "md5_of_hex_upper": hashlib.md5(h.upper().encode()).hexdigest(),
        "sha1_of_der": sha1_d,
        "sha256_of_der": sha256_d,
        "md5_of_sha1_hex": hashlib.md5(sha1_d.encode()).hexdigest(),
        "md5_of_sha256_hex": hashlib.md5(sha256_d.encode()).hexdigest(),
        "sha1_hex_as_str": sha1_d,
        "sha256_hex_as_str": sha256_d,
    }

f_fenbi = forms("FENBI", cert)
with open(FENBI_OUT, "wb") as f:
    f.write(cert)
with open(TEST_DER, "rb") as f:
    der_test = f.read()
f_test = forms("TEST", der_test)

out = {"FENBI": f_fenbi, "TEST": f_test}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)

for tag, fo in out.items():
    print(f"\n[{tag}] der_len={fo['der_len']}")
    for k, v in fo.items():
        if k not in ("hex_lower", "hex_upper", "tag"):
            print(f"  {k} = {v}")
    print("  hex_lower[:64] =", fo["hex_lower"][:64], "...")
