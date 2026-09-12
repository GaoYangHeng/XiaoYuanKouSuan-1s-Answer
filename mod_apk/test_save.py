from loguru import logger
logger.remove()

from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = r"f:\traework_main workspace\xiaoyuan-kousuan-re\apk\com.fenbi.android.leo.apk"

a = APK(APK_PATH)
dexs = list(a.get_all_dex())

# 测试：解析 dex[6]，然后序列化，比较字节
d = DEX(dexs[6])
buff = d.save()
print("原始 dex[6] 长度:", len(dexs[6]))
print("序列化后长度:", len(buff))
print("是否一致:", bytes(dexs[6]) == bytes(buff))

# 看 DEX 的类数量
print("dex[6] 类数:", len(d.classes))
