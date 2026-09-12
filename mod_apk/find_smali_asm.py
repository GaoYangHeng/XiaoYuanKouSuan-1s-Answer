import zipfile
import os

root = r"F:\Android\Sdk"
target = "com/android/tools/smali/smali/Main.class"

hits = []
for dp, dn, fn in os.walk(root):
    for f in fn:
        if f.endswith(".jar"):
            p = os.path.join(dp, f)
            try:
                with zipfile.ZipFile(p) as z:
                    if target in z.namelist():
                        hits.append(p)
            except Exception:
                pass

print("含 smali 汇编器 Main 的 jar:")
for h in hits:
    print(" ", h)
if not hits:
    print("  无")
