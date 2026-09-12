from loguru import logger
logger.remove()

from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = r"f:\traework_main workspace\xiaoyuan-kousuan-re\apk\com.fenbi.android.leo.apk"
a = APK(APK_PATH)
dexs = list(a.get_all_dex())

targets = {
    "Lcq/o;": "签名拦截器",
    "Lp005ds/c5;": "sign 生成",
    "Lp005ds/i4;": "加密 NativeEncryptUtils",
    "Lcom/kanyun/android/solar/next/network/ApiFactory;": "OkHttp 构建点",
    "Lcom/yuanfudao/android/leo/LeoApplication;": "Application",
}

for i, db in enumerate(dexs):
    d = DEX(db)
    for t, desc in targets.items():
        c = d.get_class(t)
        if c is not None:
            print(f"dex[{i}] {t}  ({desc})")
