import requests
import zipfile
import os

TOOLS = r"f:\traework_main workspace\xiaoyuan-kousuan-re\mod_apk\tools"
os.makedirs(TOOLS, exist_ok=True)

# Google Maven：com.android.tools.smali
# fat jar classifier
VERSIONS = ["3.0.10", "3.0.9", "3.0.8", "3.0.7", "3.0.6"]


def valid(p, min_entries=50):
    if not os.path.exists(p) or os.path.getsize(p) < 50000:
        return False
    try:
        with zipfile.ZipFile(p) as z:
            return len(z.namelist()) > min_entries
    except Exception:
        return False


def dl(name, dst):
    for v in VERSIONS:
        u = f"https://maven.google.com/com/android/tools/smali/{name}/{v}/{name}-{v}-fat.jar"
        print(f"try {u}", flush=True)
        try:
            r = requests.get(u, stream=True, timeout=(15, 120), headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                print("  HTTP", r.status_code, flush=True)
                continue
            with open(dst, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            print("  size", os.path.getsize(dst), flush=True)
            if valid(dst):
                print(f"  OK {name} {v}", flush=True)
                return True
            else:
                print("  invalid", flush=True)
        except Exception as e:
            print("  fail:", e, flush=True)
    return False


dl("baksmali", os.path.join(TOOLS, "baksmali.jar"))
dl("smali", os.path.join(TOOLS, "smali.jar"))
