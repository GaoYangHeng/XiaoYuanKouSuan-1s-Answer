from loguru import logger
logger.remove()

from androguard.core.dex import DEX

TARGET = "Lcom/yuanfudao/android/leo/webview/ui/activity/SimpleWebAppFireworkActivity;"

for name in ["work/classes7_patched.dex", "work/classes7.dex"]:
    d = DEX(open(name, "rb").read())
    c = d.get_class(TARGET)
    print(f"\n=== {name} ===")
    m = None
    for mm in c.get_methods():
        if mm.get_name() == "onCreate":
            m = mm
            break
    bc = m.get_code().get_bc()
    ins = list(bc.get_instructions())
    print("onCreate 指令数:", len(ins))
    for i in ins[:4]:
        print("  ", i.get_name(), i.get_output())
