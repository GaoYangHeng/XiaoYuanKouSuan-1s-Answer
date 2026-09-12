import subprocess
import zipfile
import os
import shutil

BT = r"F:\Android\Sdk\build-tools\30.0.3"
PLATFORM = r"F:\Android\Sdk\platforms\android-34\android.jar"
WORK = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\testapp"
SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"
GADGET = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\frida-gadget.so"
CONFIG = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\testapp\libgadget.config.so"

os.chdir(WORK)


def run(cmd):
    print(">", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("STDOUT:", r.stdout[-2000:])
        print("STDERR:", r.stderr[-2000:])
        raise SystemExit(f"command failed: {cmd[0]}")
    return r


# 1. 清理 + 编译
shutil.rmtree(os.path.join(WORK, "classes"), ignore_errors=True)
os.makedirs(os.path.join(WORK, "classes"), exist_ok=True)
srcs = []
for root, _dirs, files in os.walk(os.path.join(WORK, "src")):
    for f in files:
        if f.endswith(".java"):
            srcs.append(os.path.join(root, f))
run(["javac", "--release", "8", "-classpath", PLATFORM, "-d", os.path.join(WORK, "classes")] + srcs)

# 2. d8
classfiles = []
for root, _dirs, files in os.walk(os.path.join(WORK, "classes")):
    for f in files:
        if f.endswith(".class"):
            classfiles.append(os.path.join(root, f))
run(["java", "-cp", os.path.join(BT, "lib", "d8.jar"), "com.android.tools.r8.D8",
     "--release", "--lib", PLATFORM, "--output", WORK] + classfiles)

# 3. aapt2 link
run([os.path.join(BT, "aapt2.exe"), "link", "-o", os.path.join(WORK, "base.apk"),
     "-I", PLATFORM, "--manifest", os.path.join(WORK, "AndroidManifest.xml")])

# 4. 添加文件
with zipfile.ZipFile(os.path.join(WORK, "base.apk"), "a") as z:
    z.write(os.path.join(WORK, "classes.dex"), "classes.dex")
    z.write(SO, "lib/armeabi-v7a/libRequestEncoder.so")
print("added files")

# 5. zipalign
run([os.path.join(BT, "zipalign.exe"), "-f", "4",
     os.path.join(WORK, "base.apk"), os.path.join(WORK, "aligned.apk")])

# 6. 签名
ks = os.path.join(WORK, "key.jks")
if not os.path.exists(ks):
    run(["keytool", "-genkeypair", "-v", "-keystore", ks, "-alias", "sign",
         "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
         "-storepass", "android", "-keypass", "android", "-dname", "CN=Test"])
run([os.path.join(BT, "apksigner.bat"), "sign", "--ks", ks,
     "--ks-pass", "pass:android", "--key-pass", "pass:android",
     "--out", os.path.join(WORK, "signprobe.apk"), os.path.join(WORK, "aligned.apk")])

print("DONE:", os.path.join(WORK, "signprobe.apk"))
