import subprocess
import zipfile
import os
import shutil

BT = r"F:\Android\Sdk\build-tools\30.0.3"
PLATFORM = r"F:\Android\Sdk\platforms\android-34\android.jar"
WORK = r"f:\traework_main workspace\xiaoyuan-kousuan-re\mod_apk"
APK = r"f:\traework_main workspace\xiaoyuan-kousuan-re\apk\com.fenbi.android.leo.apk"
KEYSTORE = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\testapp\key.jks"
SO_PATCHED = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\libRequestEncoder_patched.so"

SMALI_LIB = r"F:\Android\Sdk\cmdline-tools\latest\lib\external\com\android\tools\smali"
DEXLIB_CP = ";".join([
    os.path.join(SMALI_LIB, "smali-dexlib2", "3.0.3", "smali-dexlib2-3.0.3.jar"),
    os.path.join(SMALI_LIB, "smali-util", "3.0.3", "smali-util-3.0.3.jar"),
    r"F:\Android\Sdk\cmdline-tools\latest\lib\external\com\google\guava\guava\31.1-jre\guava-31.1-jre.jar",
    r"F:\Android\Sdk\cmdline-tools\latest\lib\external\com\beust\jcommander\1.78\jcommander-1.78.jar",
    r"F:\Android\Sdk\cmdline-tools\latest\lib\external\com\google\guava\listenablefuture\9999.0-empty-to-avoid-conflict-with-guava\listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar",
])

os.chdir(WORK)


def run(cmd):
    print(">", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("STDOUT:", r.stdout[-3000:])
        print("STDERR:", r.stderr[-3000:])
        raise SystemExit(f"command failed: {cmd[0]}")
    return r


# 0. 提取 classes2.dex / classes3.dex / classes6.dex / classes7.dex
with zipfile.ZipFile(APK, "r") as z:
    for name in ("classes2.dex", "classes3.dex", "classes6.dex", "classes7.dex"):
        data = z.read(name)
        out = os.path.join(WORK, "work", name)
        with open(out, "wb") as f:
            f.write(data)
        print("extracted", name, len(data))

# 1. 编译桩类（ds + qp + okhttp3）
shutil.rmtree(os.path.join(WORK, "stub_classes"), ignore_errors=True)
os.makedirs(os.path.join(WORK, "stub_classes"), exist_ok=True)
stub_srcs = []
for root, _, files in os.walk(os.path.join(WORK, "stub")):
    for fn in files:
        if fn.endswith(".java"):
            stub_srcs.append(os.path.join(root, fn))
run(["javac", "-encoding", "UTF-8", "--release", "8", "-classpath", PLATFORM, "-d", os.path.join(WORK, "stub_classes")] + stub_srcs)
print("stub compiled")

# 2. 编译核心类
shutil.rmtree(os.path.join(WORK, "classes"), ignore_errors=True)
os.makedirs(os.path.join(WORK, "classes"), exist_ok=True)
core_srcs = [
    os.path.join(WORK, "src", "com", "fenbi", "android", "leo", "pk", "PkFloatButton.java"),
    os.path.join(WORK, "src", "com", "fenbi", "android", "leo", "pk", "PkAnswerEngine.java"),
    os.path.join(WORK, "src", "com", "fenbi", "android", "leo", "pk", "PkHelper.java"),
]
cp = PLATFORM + ";" + os.path.join(WORK, "stub_classes")
run(["javac", "-encoding", "UTF-8", "--release", "8", "-classpath", cp, "-d", os.path.join(WORK, "classes")] + core_srcs)
print("core compiled")

# 3. d8 编译核心类 -> pk.dex
core_classfiles = []
pk_dir = os.path.join(WORK, "classes", "com", "fenbi", "android", "leo", "pk")
for fn in os.listdir(pk_dir):
    if fn.endswith(".class"):
        core_classfiles.append(os.path.join(pk_dir, fn))
run(["java", "-cp", os.path.join(BT, "lib", "d8.jar"), "com.android.tools.r8.D8",
     "--release", "--lib", PLATFORM, "--lib", os.path.join(WORK, "stub_classes"),
     "--output", WORK] + core_classfiles)
pk_dex = os.path.join(WORK, "work", "pk.dex")
if os.path.exists(pk_dex):
    os.remove(pk_dex)
os.rename(os.path.join(WORK, "classes.dex"), pk_dex)
print("pk.dex generated")

# 4. 编译 PatchDex2 / PatchDex3
out_dir = os.path.join(WORK, "work", "out")
shutil.rmtree(out_dir, ignore_errors=True)
os.makedirs(out_dir, exist_ok=True)
run(["javac", "-encoding", "UTF-8", "-cp", DEXLIB_CP, "-d", out_dir,
     os.path.join(WORK, "work", "PatchDex2.java"),
     os.path.join(WORK, "work", "PatchDex3.java"),
     os.path.join(WORK, "work", "PatchDex4.java"),
     os.path.join(WORK, "work", "PatchDex5.java"),
     os.path.join(WORK, "work", "PatchDex6.java")])
print("patch tools compiled")

# 5. 运行 PatchDex2（classes7 注入 attach）
run(["java", "-cp", DEXLIB_CP + ";" + out_dir, "PatchDex2",
     os.path.join(WORK, "work", "classes7.dex"),
     os.path.join(WORK, "work", "classes7_patched.dex")])

# 6. 运行 PatchDex3（classes3 注入 interceptResponse）
run(["java", "-cp", DEXLIB_CP + ";" + out_dir, "PatchDex3",
     os.path.join(WORK, "work", "classes3.dex"),
     os.path.join(WORK, "work", "classes3_patched.dex")])

# 6.2 运行 PatchDex5（classes3 修复 android_id 读取）
run(["java", "-cp", DEXLIB_CP + ";" + out_dir, "PatchDex5",
     os.path.join(WORK, "work", "classes3_patched.dex"),
     os.path.join(WORK, "work", "classes3_final.dex")])

# 6.5 运行 PatchDex4（classes6 修正 vendor）
run(["java", "-cp", DEXLIB_CP + ";" + out_dir, "PatchDex4",
     os.path.join(WORK, "work", "classes6.dex"),
     os.path.join(WORK, "work", "classes6_patched.dex")])

# 6.6 运行 PatchDex6（classes2 强制隐私Gate1 + classes6 强制隐私Gate2）
run(["java", "-cp", DEXLIB_CP + ";" + out_dir, "PatchDex6",
     os.path.join(WORK, "work", "classes2.dex"),
     os.path.join(WORK, "work", "classes2_final.dex")])
run(["java", "-cp", DEXLIB_CP + ";" + out_dir, "PatchDex6",
     os.path.join(WORK, "work", "classes6_patched.dex"),
     os.path.join(WORK, "work", "classes6_final.dex")])

# 7. 复制原 APK，替换 classes3.dex / classes7.dex + 添加 classes9.dex
patched_apk = os.path.join(WORK, "work", "patched_unsigned.apk")
shutil.copy(APK, patched_apk)
tmp = patched_apk + ".tmp"
with zipfile.ZipFile(APK, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "classes2.dex":
            data = open(os.path.join(WORK, "work", "classes2_final.dex"), "rb").read()
            print("replaced classes2.dex")
        elif item.filename == "classes3.dex":
            data = open(os.path.join(WORK, "work", "classes3_final.dex"), "rb").read()
            print("replaced classes3.dex")
        elif item.filename == "classes6.dex":
            data = open(os.path.join(WORK, "work", "classes6_final.dex"), "rb").read()
            print("replaced classes6.dex")
        elif item.filename == "classes7.dex":
            data = open(os.path.join(WORK, "work", "classes7_patched.dex"), "rb").read()
            print("replaced classes7.dex")
        elif item.filename == "lib/armeabi-v7a/libRequestEncoder.so":
            data = open(SO_PATCHED, "rb").read()
            print("replaced libRequestEncoder.so (delta=0 patch)")
        zout.writestr(item, data)
    zout.write(os.path.join(WORK, "work", "pk.dex"), "classes9.dex")
    print("added classes9.dex")
os.replace(tmp, patched_apk)

# 8. zipalign（-p 对未压缩 .so 页对齐，防 extractNativeLibs=false 校验失败）
aligned = os.path.join(WORK, "work", "patched_aligned.apk")
run([os.path.join(BT, "zipalign.exe"), "-f", "-p", "4", patched_apk, aligned])

# 9. 签名
signed = os.path.join(WORK, "work", "patched_signed.apk")
if not os.path.exists(KEYSTORE):
    raise SystemExit("keystore not found: " + KEYSTORE)
run([os.path.join(BT, "apksigner.bat"), "sign", "--ks", KEYSTORE,
     "--ks-pass", "pass:android", "--key-pass", "pass:android",
     "--out", signed, aligned])

print("DONE:", signed)
