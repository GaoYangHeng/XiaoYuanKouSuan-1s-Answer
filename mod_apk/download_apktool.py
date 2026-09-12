import requests
import zipfile
import os

DST = r"f:\traework_main workspace\xiaoyuan-kousuan-re\mod_apk\tools\apktool.jar"
os.makedirs(os.path.dirname(DST), exist_ok=True)

JAR = "https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar"
MIRRORS = [
    f"https://ghfast.top/{JAR}",
    f"https://gh.ddlc.top/{JAR}",
    f"https://gh-proxy.com/{JAR}",
    f"https://ghproxy.net/{JAR}",
    f"https://gh.llkk.cc/{JAR}",
]


def valid(p):
    if not os.path.exists(p) or os.path.getsize(p) < 100000:
        return False
    try:
        with zipfile.ZipFile(p) as z:
            return len(z.namelist()) > 100
    except Exception:
        return False


for u in MIRRORS:
    print("try", u, flush=True)
    try:
        r = requests.get(u, stream=True, timeout=(15, 120), headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        with open(DST, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
        print("  size", os.path.getsize(DST), flush=True)
        if valid(DST):
            print("  OK valid jar", flush=True)
            break
        else:
            print("  invalid, next", flush=True)
    except Exception as e:
        print("  fail:", e, flush=True)
else:
    print("ALL FAILED", flush=True)
