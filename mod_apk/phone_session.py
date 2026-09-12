# NOTE: references mod_apk/work/ which is not included in the repo (gitignored).
# -*- coding: utf-8 -*-
# 一次性手机会话脚本（p2）：安装 → 启动 → 登录监控 → PK 页悬浮按钮 → 答题提交 → 汇总
# 严守 3 次连接预算：单次运行收集全部信息；任何单点异常都不阻断最终汇总
# 审查修复：stderr合并(P0)/UTF8输出(P1)/异常兜底+finally汇总(P1)/多设备-s(P2)/match独立判(P2)/WAKEUP等
import subprocess, threading, time, os, sys, re

for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PKG = "com.fenbi.android.leo"
APK = r"f:\traework_main workspace\xiaoyuan-kousuan-re\mod_apk\work\patched_signed.apk"
STAMP = time.strftime("%Y%m%d_%H%M%S")
OUT = os.path.join(r"f:\traework_main workspace\xiaoyuan-kousuan-re\mod_apk\work", "session_" + STAMP)
os.makedirs(OUT, exist_ok=True)
LOG = os.path.join(OUT, "logcat_full.txt")
SERIAL = None


def adb(*args, timeout=60):
    try:
        r = subprocess.run(["adb"] + list(args), stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return (r.stdout or "").strip()
    except subprocess.TimeoutExpired:
        return "[TIMEOUT] adb " + " ".join(args)
    except FileNotFoundError:
        sys.exit("adb 不在 PATH，中止")


def adbs(*args, timeout=60):
    return adb("-s", SERIAL, *args, timeout=timeout)


def shot(name):
    for _ in range(2):
        try:
            r = subprocess.run(["adb", "-s", SERIAL, "exec-out", "screencap", "-p"],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30)
            if r.returncode == 0 and r.stdout and len(r.stdout) > 1000:
                png = os.path.join(OUT, name + ".png")
                with open(png, "wb") as f:
                    f.write(r.stdout)
                print("  [截屏] " + png)
                return
        except Exception as e:
            print("  [截屏异常] %s: %s" % (name, e))
        time.sleep(2)
    print("  [截屏失败] " + name + "（不阻断会话，继续）")


def pause(msg):
    print("\n=== " + msg + " ===")
    try:
        input("  完成后回车继续（直接回车=已就绪）...")
    except EOFError:
        print("  [警告] stdin 不可用，pause 自动跳过——截屏时点可能不准")


CODE_PAT = re.compile(r"PkHelper.*(RESP|ERROR) (\d{3})")
hits = {"codes": [], "match": 0, "crash": []}


def logcat_reader(p):
    try:
        with open(LOG, "w", encoding="utf-8", errors="replace") as f:
            for line in p.stdout:
                f.write(line)
                f.flush()
                if "PkHelper" in line:
                    m = CODE_PAT.search(line)
                    if m:
                        hits["codes"].append(m.group(2))
                        print("  >>> [验证点] " + line.strip(), flush=True)
                    else:
                        print("  >>> " + line.strip(), flush=True)
                if "/math/pk/match" in line:
                    hits["match"] += 1
                    print("  >>> [match线索] " + line.strip(), flush=True)
                if "FATAL EXCEPTION" in line or "SIGSEGV" in line:
                    hits["crash"].append(line.strip())
                    print("  !!! [崩溃] " + line.strip(), flush=True)
    except Exception as e:
        print("  [logcat线程异常] " + str(e), flush=True)


def summarize():
    print("\n[6/6] ===== 自动汇总 =====")
    try:
        print("RESP/ERROR 状态码序列: " + (",".join(hits["codes"]) if hits["codes"] else "(无)"))
        c417 = hits["codes"].count("417")
        if hits["codes"]:
            print("417 出现: %d 次 %s" % (c417, "→ [X] 仍被拒" if c417 else "→ [OK] 未复现"))
        else:
            print("417 判定: PkHelper 无登录流量日志（登录接口URL可能不含auth/login关键词）→ 以 02 截屏人工确认")
        print("match 线索行: %d（注：match 成功时 PkHelper 不打日志，仅 4xx ERROR 才出现 → 以 04 截屏 Toast 为准）" % hits["match"])
        print("崩溃: " + ("; ".join(hits["crash"][:3]) if hits["crash"] else "无 [OK]"))
        if os.path.exists(LOG):
            lg = open(LOG, encoding="utf-8", errors="replace").read()
            open(os.path.join(OUT, "PkHelper_only.txt"), "w", encoding="utf-8").write(
                "\n".join(l for l in lg.splitlines() if "PkHelper" in l))
            cand = [l.strip() for l in lg.splitlines() if " 417 " in l or "=417" in l][:5]
            print("全量日志 417 线索(前5): " + ("; ".join(cand) if cand else "无"))
        print("全部产物: " + OUT)
        print("最终判据: 417=0 + 02截屏登录成功 + 04截屏Toast「已提交」→ sign 修复成立")
    except Exception as e:
        print("[汇总异常] " + str(e) + "；原始日志: " + LOG)


print("== p2 一次性会话 " + STAMP + " ==")
devs = adb("devices")
print(devs)
rows = [l for l in devs.splitlines()[1:] if l.strip() and "\t" in l]
online = [l.split("\t")[0].strip() for l in rows if l.split("\t")[1].strip() == "device"]
if not online:
    sys.exit("无在线设备（unauthorized/offline 不算），中止（不消耗连接预算）")
if len(online) > 1:
    sys.exit("检测到多台设备 " + str(online) + "，请只保留目标机后再跑（不消耗预算）")
SERIAL = online[0]
print("目标设备: " + SERIAL)

p = None
try:
    print("\n[1/6] 安装 APK（-r 覆盖，-t 允许 test 签名）...")
    inst = adbs("install", "-r", "-t", APK, timeout=180)
    print(inst)
    if "INSTALL_FAILED" in inst:
        print("安装失败（签名冲突/降级等）→ 卸载重装（清掉手机上旧版数据，属预期代价）")
        print(adbs("uninstall", PKG))
        inst = adbs("install", "-r", "-t", APK, timeout=180)
        print(inst)
    if "Success" not in inst:
        sys.exit("安装失败且未恢复，中止会话（本次连接已计入预算，先离线修好再连）")

    print("\n[2/6] 清 logcat 并启动后台监控 → " + LOG)
    adbs("logcat", "-c")
    p = subprocess.Popen(["adb", "-s", SERIAL, "logcat", "-v", "time"],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         text=True, encoding="utf-8", errors="replace")
    threading.Thread(target=logcat_reader, args=(p,), daemon=True).start()
    time.sleep(1)

    print("\n[3/6] 亮屏并启动 app...")
    adbs("shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(1)
    print(adbs("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1"))
    time.sleep(6)
    shot("01_launch")
    pause("若在锁屏请先解锁。请在手机上完成登录（输账号→登录）。留意实时输出的 [验证点] 行")

    print("\n[4/6] 登录阶段结束")
    shot("02_after_login")
    time.sleep(2)

    pause("请进入：口算PK → 比大小 → 开始匹配（等题目出现）。悬浮按钮应出现在右下角")
    shot("03_pk_page")
    time.sleep(2)

    pause("点击「1秒答题」后【立刻回车】（Toast 只显示几秒）。若失败可点「复制报错」")
    shot("04_after_submit")
    time.sleep(1)
    shot("05_submit_backup")
finally:
    if p is not None:
        p.terminate()
        try:
            p.wait(timeout=5)
        except Exception:
            pass
    time.sleep(0.5)
    summarize()
