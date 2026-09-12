import zipfile
import os

APK = r"f:\traework_main workspace\xiaoyuan-kousuan-re\apk\com.fenbi.android.leo.apk"
OUT = r"f:\traework_main workspace\xiaoyuan-kousuan-re\so_dump"

os.makedirs(OUT, exist_ok=True)
with zipfile.ZipFile(APK, "r") as z:
    for name in z.namelist():
        if "libRequestEncoder" in name or "RequestEncoder" in name:
            data = z.read(name)
            out_path = os.path.join(OUT, name.replace("/", "_"))
            with open(out_path, "wb") as f:
                f.write(data)
            print(name, len(data), "->", out_path)
        elif name.startswith("lib/") and name.endswith(".so"):
            print("  (other so)", name)
