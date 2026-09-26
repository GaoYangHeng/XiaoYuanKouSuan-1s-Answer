# 改动日志

本项目所有成品 APK 的版本变更记录。旧版本文件永久保留在 [`release/`](release/) 目录，不做删除。

## [3.143.1] — 2026-09-26

成品：[`release/xiaoyuan-kousuan-1s-answer-3.143.1.apk`](release/xiaoyuan-kousuan-1s-answer-3.143.1.apk)（约 87 MB）

### 新增
- **全量移植到官方 3.143.1**（旧版基于官方 3.141.1 / v52），官方签名 `CN=fenbi` 校验通过。
- **设置面板**：可拖动悬浮按钮下方新增「⚙ 设置」小条，点击弹出设置窗口，设置即时保存（SharedPreferences）：
  - **单局时间**：1–60 秒（默认 2 秒），按「目标耗时 ÷ 题数 − H5 固定开销」换算每题回调延迟；
  - **人类化笔记**开关：关闭后为机械笔迹（无抖动、最快步进）；
  - **笔记强度**：0–100%（默认 50%），控制笔迹坐标抖动幅度；
  - **匹配失败重试间隔**：3–30 秒（默认 3 秒，防触发服务端限流）；
  - **自动开启**：进入 PK 页免点按钮直接武装；
  - **界面提示** Toast 开关（日志不受影响）。
  - **三种退出方式**：右上角 ✕、系统返回键、点击窗口外空白区域。
- 悬浮按钮布局更新：`1秒答题` / `复制报错` / `⚙ 设置` 小条（可整体拖动）。

### 修复
- **启动即崩溃 `VerifyError: invalid branch target`**（仅新版官方包触发）：拦截器补丁原实现往
  `intercept()` 的 `return-object` 前插入指令，而 3.143.1 的 `np/o.intercept` 内部含跨越插入点的
  前向分支（dex 分支为相对 codeOffset），插入后偏移不重算导致 ART 校验器拒载。
  改为「原方法整体改名 `intercept_orig`（一字不动）+ 新建零分支顺序转发方法」，彻底规避分支重算问题。
- **match 密文解密失败 `NoClassDefFoundError: Lds/i4`**：contentcoder 解密类随官方混淆漂移
  `ds.i4` → `nr.i4`（定位链：`loadLibrary("ContentEncoder")` → native `c([B)[B` → 调用方），
  已同步 `PkAnswerEngine` 全部引用与诊断日志中的 `ds.i3` → `nr.i3`。
- **匹配失败重试空转 `RETRY no-fn`**：匹配失败页是新 document，`HOOK_JS` 随旧页面销毁，
  `window.__pkRetryMatch` 不存在。现每次重试前先幂等重注入 `HOOK_JS`。

### 变更
- 补丁点全部随 3.143.1 混淆重排重新定位（调用图逐一比对确认）：

  | 补丁 | 旧（3.141.1） | 新（3.143.1） |
  |---|---|---|
  | 悬浮按钮挂载 | `SimpleWebAppFireworkActivity.onCreate` | 不变 |
  | 响应拦截 | `cq/v.intercept` | `np/o.intercept` |
  | 渠道 vendor | `xd0/f.q` | `hd0/f.q` |
  | android_id 直读 | `hn0/b.e` | `sm0/b.e` |
  | 隐私门强制通过 | `tg/n.b` + `hn0/a.a` | `Leg/n.b` + `xc/c.a` |

- 签名 so 更新为 3.143.1 版 `libRequestEncoder.so`（重新打 delta=0 补丁，补丁区指令结构
  与旧版逐字节核对一致：`mla/muls/mla + ldr r0,[sp,#0x14] + str r4,[r0]`）。
- `mod_apk/` 构建工程同步：`build.py`、`src/`（含新增 `PkSettings.java`、`PkSettingsDialog.java`）、`stub/nr/i4.java`。

### 真机验证（ELZ-AN10 / Android 14）
- 启动无崩溃，登录态保持；全部接口 `vendor=tencent`、`sign` 服务端接受（match/v2 HTTP 200）。
- 完整一局：30 题全部答对（`correctCnt=30`）、`costTime=3495ms`、服务端落库；
  人类化笔迹坐标带抖动小数真实上报（`script` 字段）。
- 设置面板六项显示、三种退出方式逐一验证通过。

## [v52 / 3.141.1] — 2026-09-18

成品：[`release/xiaoyuan-kousuan-1s-answer-v52.apk`](release/xiaoyuan-kousuan-1s-answer-v52.apk)（约 82 MB）

- 首个发布版本，基于官方 3.141.1 重打包。
- **1 秒答题悬浮按钮**：进对局页点一下开启，自动抓取 match 响应中的答案、合成笔迹、劫持识别桥、
  自动判题并走官方链路提交。
- 构建期补丁：so patch（去签名指纹）、DEX 注入（attach / 响应拦截 / vendor 修正 /
  android_id 直读 / 隐私门强制通过）、自签名重打包。
- 附完整逆向资料：[`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md)、[`opensource/snippets/`](opensource/snippets/)、
  [`reports/`](reports/)。
