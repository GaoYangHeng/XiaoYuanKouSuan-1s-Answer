$ErrorActionPreference = "Stop"
$BT = "F:\Android\Sdk\build-tools\30.0.3"
$PLATFORM = "F:\Android\Sdk\platforms\android-34\android.jar"
$WORK = "f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\testapp"
$SO = "f:\traework_main workspace\xiaoyuan-kousuan-re\decompiled\sources\resources\lib\armeabi-v7a\libRequestEncoder.so"

Set-Location $WORK

# 1. 编译 Java
New-Item -ItemType Directory -Force -Path "$WORK\classes" | Out-Null
$srcs = Get-ChildItem "$WORK\src" -Recurse -Filter *.java | ForEach-Object { $_.FullName }
javac --release 8 -classpath $PLATFORM -d "$WORK\classes" $srcs
if ($LASTEXITCODE -ne 0) { throw "javac failed" }

# 2. d8 -> classes.dex（直接用 java 调 d8.jar，绕过 find_java 问题）
$classfiles = Get-ChildItem "$WORK\classes" -Recurse -Filter *.class | ForEach-Object { $_.FullName }
java -cp "$BT\lib\d8.jar" com.android.tools.r8.D8 --release --lib $PLATFORM --output "$WORK" $classfiles
if ($LASTEXITCODE -ne 0) { throw "d8 failed" }

# 3. aapt2 link -> base.apk
& "$BT\aapt2.exe" link -o "$WORK\base.apk" -I $PLATFORM --manifest "$WORK\AndroidManifest.xml"
if ($LASTEXITCODE -ne 0) { throw "aapt2 link failed" }

# 4. 用 python 把 classes.dex 和 so 塞进 APK
python -c @"
import zipfile
apk = r'$WORK\base.apk'
so = r'$SO'
with zipfile.ZipFile(apk, 'a') as z:
    z.write(r'$WORK\classes.dex', 'classes.dex')
    z.write(so, 'lib/armeabi-v7a/libRequestEncoder.so')
print('added dex + so')
"@

# 5. zipalign
& "$BT\zipalign.exe" -f 4 "$WORK\base.apk" "$WORK\aligned.apk"
if ($LASTEXITCODE -ne 0) { throw "zipalign failed" }

# 6. 生成密钥（若不存在）
if (-not (Test-Path "$WORK\key.jks")) {
    keytool -genkeypair -v -keystore "$WORK\key.jks" -alias sign -keyalg RSA -keysize 2048 -validity 10000 -storepass android -keypass android -dname "CN=Test"
}

# 7. 签名
& "$BT\apksigner.bat" sign --ks "$WORK\key.jks" --ks-pass pass:android --key-pass pass:android --out "$WORK\signprobe.apk" "$WORK\aligned.apk"
if ($LASTEXITCODE -ne 0) { throw "apksigner failed" }

Write-Output "DONE: $WORK\signprobe.apk"
