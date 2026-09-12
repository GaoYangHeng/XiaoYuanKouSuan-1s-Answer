# NOTE: references mod_apk/work/ which is not included in the repo (gitignored).
import zipfile
import hashlib

APK = r"f:\traework_main workspace\xiaoyuan-kousuan-re\mod_apk\work\patched_a_signed.apk"
ORIG = r"f:\traework_main workspace\xiaoyuan-kousuan-re\apk\com.fenbi.android.leo.apk"

def list_meta(path, label):
    print("=== %s META-INF ===" % label)
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if "META-INF" in n.upper() and (n.endswith(".RSA") or n.endswith(".SF") or n.endswith(".MF") or n.endswith(".DSA")):
                data = z.read(n)
                md5 = hashlib.md5(data).hexdigest()
                print("  %s (%d bytes) md5=%s" % (n, len(data), md5))

list_meta(ORIG, "ORIG")
list_meta(APK, "PATCHED")
