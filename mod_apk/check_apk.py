# NOTE: references mod_apk/work/ which is not included in the repo (gitignored).
# -*- coding: utf-8 -*-
# APK 交付终检：条目零丢失 + 替换产物字节一致 + 确实替换（≠原版）+ manifest 在
import zipfile

ORIG = r"f:\traework_main workspace\xiaoyuan-kousuan-re\apk\com.fenbi.android.leo.apk"
MOD = r"f:\traework_main workspace\xiaoyuan-kousuan-re\mod_apk\work\patched_signed.apk"
WORK = r"f:\traework_main workspace\xiaoyuan-kousuan-re\mod_apk\work"
SO = r"f:\traework_main workspace\xiaoyuan-kousuan-re\crack_sign\libRequestEncoder_patched.so"

# (APK内条目, 期望来源, 是否必须≠原版)
PLAN = [
    ("classes2.dex", WORK + r"\classes2_final.dex", True),
    ("classes3.dex", WORK + r"\classes3_final.dex", True),
    ("classes6.dex", WORK + r"\classes6_final.dex", True),
    ("classes7.dex", WORK + r"\classes7_patched.dex", True),
    ("classes9.dex", WORK + r"\pk.dex", False),  # 新增条目，原版没有
    ("lib/armeabi-v7a/libRequestEncoder.so", SO, True),
]

zo = zipfile.ZipFile(ORIG)
zm = zipfile.ZipFile(MOD)
names_o = set(zo.namelist())
names_m = set(zm.namelist())
print("原 APK 条目数: %d, 改包条目数: %d" % (len(names_o), len(names_m)))
lost = names_o - names_m
# META-INF 旧签名(FENBI.*)被 apksigner 剥离并以 SIGN.* 重签，属预期行为不算丢失
lost = {n for n in lost if not n.startswith("META-INF/")}
added = names_m - names_o
print("丢失条目: %s" % (sorted(lost) if lost else "无 ✅"))
print("新增条目: %s" % (sorted(added) if added else "无"))

bad = zm.testzip()
print("zip 完整性(testzip): %s" % ("损坏:" + bad if bad else "OK ✅"))
print("AndroidManifest.xml 在包内: %s" % ("✅" if "AndroidManifest.xml" in names_m else "❌ 丢失!"))

fails = 0
for entry, src, must_diff in PLAN:
    if entry not in names_m:
        print("❌ %s 不在 APK 内" % entry); fails += 1; continue
    a = zm.read(entry)
    b = open(src, "rb").read()
    same_src = (a == b)
    diff_orig = True
    if entry in names_o:
        diff_orig = (a != zo.read(entry))
    ok = same_src and (diff_orig if must_diff else True)
    print("%s %s: 与源产物一致=%s, ≠原版=%s, 大小=%d" %
          ("✅" if ok else "❌", entry, same_src, diff_orig, len(a)))
    if not ok:
        fails += 1

print("\n结论: " + ("全部通过 ✅" if fails == 0 and not lost else "存在 %d 项失败 ❌" % (fails + len(lost))))
raise SystemExit(0 if fails == 0 and not lost else 1)
