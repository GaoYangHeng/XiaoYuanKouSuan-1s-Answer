import requests
import zipfile
import os

TOOLS = r"f:\traework_main workspace\xiaoyuan-kousuan-re\mod_apk\tools"
os.makedirs(TOOLS, exist_ok=True)

# google/smali release 的 fat jar（smali 汇编器）
ASSETS = [
    "https://github.com/google/smali/releases/download/3.0.8/smali-3.0.8-fat.jar",
    "https://github.com/google/smali/releases/download/v3.0.8/smali-3.0.8-fat.jar",
    "https://github.com/google/smali/releases/download/3.0.7/smali-3.0.7-fat.jar",
    "https://github.com/google/smali/releases/download/v3.0.7/smali-3.0.7-fat.jar",
]
HOSTS = ["ghfast.top", "gh.ddlc.top", "gh-proxy.com"]


def valid(p):
    if not os.path.exists(p) or os.path.getsize(p) < 50000:
        return False
    try:
        with zipfile.ZipFile(p) as z:
            return len(z.namelist()) > 50
    except Exception:
        return False


dst = os.path.join(TOOLS, "smali.jar")
for asset in ASSETS:
    for host in HOSTS:
        u = f"https://{host}/{asset}"
        print("try", u, flush=True)
        try:
            r = requests.get(u, stream=True, timeout=(10, 90), headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                print("  HTTP", r.status_code, flush=True)
                continue
            with open(dst, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            print("  size", os.path.getsize(dst), flush=True)
            if valid(dst):
                print("OK smali.jar", flush=True)
                raise SystemExit(0)
            else:
                print("  invalid", flush=True)
        except SystemExit:
            raise
        except Exception as e:
            print("  fail:", e, flush=True)
print("smali.jar ALL FAILED", flush=True)
