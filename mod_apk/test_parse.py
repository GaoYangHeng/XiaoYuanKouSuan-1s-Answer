from loguru import logger
logger.remove()

from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = r"f:\traework_main workspace\xiaoyuan-kousuan-re\apk\com.fenbi.android.leo.apk"

a = APK(APK_PATH)
print("包名:", a.get_package())

dexs = list(a.get_all_dex())
print("dex 数:", len(dexs))

TARGET = "Lcom/yuanfudao/android/leo/webview/ui/activity/SimpleWebAppFireworkActivity;"

for i, db in enumerate(dexs):
    d = DEX(db)
    c = d.get_class(TARGET) if hasattr(d, "get_class") else d.classes.get(TARGET)
    if c is not None:
        print(f"在 dex[{i}] 找到目标类")
        m = None
        for mm in c.get_methods():
            if mm.get_name() == "onCreate":
                m = mm
                break
        if m is not None:
            print("onCreate 描述符:", m.get_descriptor())
            code = m.get_code()
            if code is not None:
                bc = code.get_bc()
                ins = list(bc.get_instructions())
                print("onCreate 指令数:", len(ins))
                for insn in ins[:10]:
                    print("  ", insn.get_name(), insn.get_output())
            else:
                print("onCreate 无 code")
        else:
            print("未找到 onCreate")
        break
else:
    print("未找到目标类")
