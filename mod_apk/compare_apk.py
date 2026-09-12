# NOTE: references mod_apk/work/ which is not included in the repo (gitignored).
import zipfile

ORIG = r"F:\traework_main workspace\xiaoyuan-kousuan-re\apk\com.fenbi.android.leo.apk"
PATCH = r"F:\traework_main workspace\xiaoyuan-kousuan-re\mod_apk\work\patched_signed.apk"

zo = zipfile.ZipFile(ORIG)
zp = zipfile.ZipFile(PATCH)

no = zo.namelist()
np_ = zp.namelist()

set_o = set(no)
set_p = set(np_)

print("原版条目数:", len(no), " 改包版条目数:", len(np_))
print("\n=== 只在原版存在 ===")
for n in sorted(set_o - set_p):
    print("  ", n)
print("\n=== 只在改包版存在 ===")
for n in sorted(set_p - set_o):
    print("  ", n)

print("\n=== 同名但内容不同（大小/CRC） ===")
diff = 0
for n in sorted(set_o & set_p):
    io = zo.getinfo(n)
    ip = zp.getinfo(n)
    if io.CRC != ip.CRC or io.file_size != ip.file_size:
        diff += 1
        if n.endswith('.dex'):
            print(f"  [DEX] {n}: 原版 {io.file_size}B CRC={io.CRC:x} -> 改包 {ip.file_size}B CRC={ip.CRC:x}")
        else:
            print(f"  {n}: 原版 {io.file_size}B -> 改包 {ip.file_size}B")
print("内容不同的文件数:", diff)

zo.close()
zp.close()
