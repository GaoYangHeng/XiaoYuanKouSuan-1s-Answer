# 技术报告：小猿口算 PK 自动答题实现原理与复刻指南

> 配套产物：`release/xiaoyuan-kousuan-1s-answer-v52.apk`
> 代码片段：`opensource/snippets/`（java / js / sign 三组，共 7 个文件）
> 适用版本：目标应用 `com.fenbi.android.leo` v52（3.141.1），armeabi-v7a
>
> **说明**：`opensource/snippets/` 中的代码为**脱敏骨架**——保留全部关键判断、字段名、常量与坑位注释，移除可直接编译的完整实现。复刻者需按本报告的坐标自行补齐实现。

---

## 0. 一句话结论

**判题在客户端本地完成**：题目下发时答案（`rightAnswers` / `expectedResult`）已随题目一起到达，客户端只做「识别出的字符串」与「正确答案」的精确相等比对（`Intrinsics.areEqual`），无服务端二次判题、无笔画几何校验。

因此实现的重心不是"骗过服务端判题"，而是三件事：

1. 在页面侧**截获题目响应**并解密拿到答案；
2. **劫持识别桥**，在原生识别器返回前就把正确答案回传；
3. 合成**看起来像人写的笔迹**（服务端会记录轨迹，假笔迹会被风控清零）。

同时，重打包后 `libRequestEncoder.so` 会因签名指纹不匹配污染请求路径（HTTP 417），需要打 patch。

---

## 1. 攻击面评估（静态分析结论）

| 防护点 | 强度 | 证据 | 对实现的影响 |
| --- | --- | --- | --- |
| 加固 / 加壳 | **无** | `AndroidManifest.xml` 直挂 `com.fenbi.android.leo.LeoApplication`，无 `StubApp`/代理壳；全局无 `jiagu`/`bangcle`/`secneo`/`libDexHelper` 特征 | 无需脱壳，直接改 DEX |
| Java 层签名/完整性校验 | **无** | `com/yuanfudao` 内 `getPackageInfo` / `GET_SIGNATURES` / `signature` **零命中** | 重打包重签名即可运行 |
| 反调试 | **无** | `TracerPid` / `isDebuggerConnected` / `ptrace` / `/proc/self/status` **零命中** | 可自由调试 |
| Xposed / Frida 检测 | **无**（Java 层） | 全局 grep 仅三方库误报 | 动态插桩可行 |
| root 检测 | **弱** | 仅 `gc0/g.java` 的 `g()` 扫描 11 个 su 路径，只用于崩溃墓碑写 `Rooted: Yes/No`，不拦截 | 无需处理 |
| 模拟器检测 | **无** | qemu / goldfish / ranchu / genymotion **零命中**（1 处为 OAID 证书 base64 误报） | 可跑模拟器 |
| Native 签名校验 | **中** | `libRequestEncoder.so` 校验应用签名指纹，不匹配则污染 path 首字节 → 服务端 417 | **必须打 patch**，见 §4 |
| 时间对齐 / 防重放 | **中** | 签名时间戳用 HTTP `Date` 头校正后的时间 | 保持系统时间准确即可 |
| 设备指纹 / 风控 | **中** | 数盟 `libdu.so` + MSA OAID；但 `shumengReportEnable` 默认 `false` | 上报默认关闭，无需额外处理 |

**总体难度：低。** 无壳、无应用级签名校验、判题本地化。

---

## 2. 目标包结构与关键文件坐标

反编译产物根目录：`decompiled/sources/sources/`（jadx 1.5.6，29362 个类）

```
com.fenbi.android.leo/       业务主包（UI、网络、判题、题目）
com.yuanfudao.android.leo/   安全/风控/图像/答题（关键逆向对象）
cn.shuzilm.core/             数盟 DU 设备指纹 SDK v8.8.3
com.bun.miitmdid/            MSA OAID SDK
p005ds/                      混淆工具类（请求签名 c5、进程判断 m3）
cq/                          okhttp 拦截器（签名 o、运行时参数 n、重试 l）
st/                          Solar SDK 初始化
gc0/                         CrashUtil（唯一 Java root 扫描）
```

### 2.1 坐标索引表

| 功能 | 类 / 方法 | 路径 |
| --- | --- | --- |
| 签名 wrapper | `c5.c().b(path)` | `p005ds/c5.java`（密钥在 L52） |
| native 签名入口 | `native String zcvsd1wr2t(String, String, int)` | `com/fenbi/android/leo/utils/e.java` |
| 签名拦截器 | `cq/o.java` | `cq/o.java` |
| 时间对齐（解析 `Date` 头） | `cq/l.java` | `cq/l.java` |
| 时间偏移存储 `time.delta` | `tg/x.java`（`x.k().s()`） | `tg/x.java` |
| 设备指纹 | `shepherd/a.java`（`shumengReportEnable=false`）、`shepherd/b.java` | `com/yuanfudao/android/leo/shepherd/` |
| 数盟 JNI | `cn/shuzilm/core/Main.java`、`DUHelper.java` | `cn/shuzilm/core/` |
| 识别器入口 | `br.d`（识别方法） | 混淆类 |
| 图像归一化 | `br.e` / `yq.e` → 128×64 灰度 | 混淆类 |
| 本地模型推理 | 本地 math TFLite 模型，输出 16×32 | — |
| 贪心解码（阈值 0.1） | `br.c` / `yq.d` | 混淆类 |
| 结果比对 | `kotlin.jvm.internal.Intrinsics.areEqual` | Kotlin 标准库 |
| 成绩提交 | `StudyExerciseResultApiService.submitExercise` | `com/yuanfudao/android/leo/study/exercise/result/StudyExerciseResultApiService.java` (L47) |
| root 扫描 | `gc0/g.g()` | `gc0/g.java` |

### 2.2 提交接口

```
POST /leo-homework/android/daily-practice/exercise/submit
POST /leo-homework/android/daily-practice/exercise/review/submit
```

### 2.3 风控埋点端点

`/debug/leo/getDidFailed`、`/debug/leo/didChanged`、`/debug/leo/abnormalTimeDelta`（时间异常）、`/debug/retryInterceptor/request401` 等，由 `wl.l.f80804a.j(...)` / `wl.e.a().log(...)` 上报。

---

## 3. 判题链路（为什么可行）

```
题目下发(rightAnswers)
  → ScriptBoard 采集笔迹（700ms 防抖 / 判空）
  → br.d 识别器
  → br.e / yq.e 转 128×64 灰度归一化
  → 本地 math TFLite 模型（输出 16×32）
  → br.c / yq.d 贪心解码（阈值 0.1）
  → Intrinsics.areEqual 精确字符串相等   ← 唯一判定点
  → StudyExerciseResultApiService 提交
```

**关键**：整条链路都在客户端。只要让"识别结果"等于"正确答案"，判定必然通过，服务端只接收最终成绩。

---

## 4. 请求签名机制与 so patch

### 4.1 调用链

```
ds.c5.c().b(path)
  → e.zcvsd1wr2t(str, "wdi4n2t8edr", (int)(x.k().s() / 1000))
  → libRequestEncoder.so（主 JNI 函数 VA 0x414E8）
```

- 签名密钥：`"wdi4n2t8edr"`（`p005ds/c5.java` L52）
- 时间戳：`(int)(x.k().s() / 1000)`，`x.k().s()` 是被 HTTP `Date` 头修正后的设备时间（防重放）；`cq/l.java` 解析响应 `Date` 头写入 `tg/x.java` 的 `time.delta`

### 4.2 签名算法（真机 5/5 命中）

```
K     = "wdi4n2t8edr"
P     = path（原样传入）
h1    = md5(P + K)
h2    = md5(P + K + h1 + P)
h3    = md5(P + K + h1 + P + h2 + T410)
final = md5(P + K + h1 + P + h2 + T410 + h3 + K)
```

`T410` = `f(ts)`：由 `.so` 偏移 `0x44280` 的编码器产出，**410 字节**的 `%lu` 十进制拼接流，只依赖时间戳。

> ⚠️ 该段无法用纯 Python 推出闭式解。可靠做法是用 Unicorn 直接模拟执行官方 `.so`（骨架见 `opensource/snippets/sign/07_sign_flow.py`）。
> ⚠️ 若看到把 T410 简化为 `str(ts // 60)` 的参考实现，那是**从未真机验证**的简化式，不可用于生产。

### 4.3 为什么会返回 417（签名指纹校验）

`libRequestEncoder.so` 内部会校验应用签名指纹：

```
MD5(0x43338 / 0x43398) → hex(0x43c04)
  → 与两枚硬编码 32 位常量比对：
      "9a2806e869bf45f85e601a69f895d213"  @0x47454
      "1dcd877d86d19882d8d055a1a87de93c"  @0x47640   （推测为正版签名指纹）
  → 不匹配则 A*B != 0 → delta != 0
  → 0x41A82: P[0] = (char)(P[0] + delta)              ← 唯一污染点
  → 服务端校验 path 失败 → HTTP 417
```

### 4.4 Patch 方案

见 `opensource/snippets/sign/06_so_patch.py`：把"污染量"的计算指令改掉，使其恒为 0。

| 项目 | 值（armeabi-v7a） |
| --- | --- |
| Patch 偏移 | `0x41A3E` |
| Patch 长度 | 10 字节 |
| 原指令 | `00 FB 04 81 60 43 00 FB 08 14` |
| 替换为 | `00 24 00 BF 00 BF 00 BF 00 BF`（`movs r4, #0` + 4×`nop`） |

> 🚩 **红线：绝对不要动 `0x41A48` / `0x41A4A`**
> ```
> 0x41A48: 05 98   ldr r0, [sp, #0x14]   ← 加载输出指针
> 0x41A4A: 04 60   str r4, [r0]          ← 写回污染量
> ```
> 早期 12 字节版本把 `ldr` 也 nop 掉，导致 `str` 用了错误指针，**真机 SIGSEGV**。patch 后应断言这两处仍为 `05 98 04 60`。
>
> 另：`.data` 首字 G1 `@0x82288 = -0x63` 静态初值恒通过，**切勿改动 `.data`**。

补充情报：`0x42D50` 是 `std::string::compare` 的包装（内部 `memcmp` + 长度决胜），不是 `getPackageInfo` 封装；全库无 `getPackageInfo` 字符串。

### 4.5 请求 URL 组装

```python
q = ("_productId=611&platform=android34&version=3.141.1&vendor=tencent"
     "&deviceCategory=phone&av=5&webviewVersion=131&whRatio=2.06"
     "&isBackground=0&sign=" + sign)
url = host + path + "?" + q
```

**PC 侧实验结论**：读接口（history / home）可用；写接口（match 系列）**始终 417**，即便复刻完整 WebView header 也无效，推测缺少 SDK 设备指纹。因此自动化只能在真机/改包内完成。

---

## 5. 题目获取：拦截 XHR / fetch

见 `opensource/snippets/java/02_hook_js.java`。在 WebView 注入脚本，劫持 `XMLHttpRequest.prototype.open/send` 与 `window.fetch`。

### 5.1 必须同时匹配两条路径（重要坑）

```javascript
u.indexOf('/pk/match')     >= 0   // 常规对局
|| u.indexOf('/multi/match') >= 0 // 8 人局：路径为 .../pk/multi/match/v2
```

> ⚠️ 8 人局路径是 `/pk/multi/match/v2`，**不包含** `/pk/match` 子串。只匹配前者会导致 8 人局抓不到题目。

### 5.2 加密响应的处理

题目接口返回**加密二进制**，需编码后交给原生解密：

```javascript
if (x.responseType === 'arraybuffer' && x.response) {
  // 逐字节转字符串后再 base64，加 'AB64:' 前缀
  t = 'AB64:' + btoa(binaryString);
} else {
  t = x.responseText;
}
```

`fetch` 分支同理：按 `content-type` 判断走 `clone().text()` 还是 `clone().arrayBuffer()`。

### 5.3 判定"题目"还是"错误"（重要坑）

错误响应是**明文 JSON**，但走 arraybuffer 分支后也会被加上 `AB64:` 前缀——**不能只看前缀**：

```javascript
raw = atob(t.substring(5));
ok  = (raw.charAt(0) !== '{');   // '{' => 明文错误(失败)；二进制 => 加密题目(成功)
```

> 早期只判断 `AB64:` 前缀就认定成功，导致匹配失败被误判为成功、重试逻辑不触发。

### 5.4 解密

```java
byte[] plain = ds.i4.a.a(raw);   // 自反变换 + GZIP
```

加密为同一系列函数的 `c()`（GZIP + 自反变换）。详见 §8。

---

## 6. 劫持识别桥（核心）

见 `opensource/snippets/js/04_recognize_hook.js`。

前端用 `signature_pad` 收集笔迹后，通过 JSBridge 调 `MathExercise_recognize` 让原生识别。**抢在原生调用之前命中，直接回传正确答案**。

### 6.1 为什么注入 `window.MathExerciseWebView` 必然生效

目标代码的 Android 分支会优先查找：

```javascript
window[Capitalize(namespace) + "WebView"]   // → window.MathExerciseWebView
```

**命中即 return，不再回落**到 `window.LeoWebView.callNative`。因此注入该对象必然被优先使用。

### 6.2 参数与字段

```javascript
var a    = (b64d(p).arguments || [])[0] || {};  // base64 解码后的参数
var ans  = a.expectedResult || [];              // ★ 正确答案数组
var t    = a.trigger;                           // ★ 回调函数名
```

### 6.3 两个关键处理

**① 题目未就绪时吞掉，不回 trigger**

```javascript
if (!t || !ans.length) { window.__pkSwallow += 1; return true; }
```

`expectedResult` 为空说明题目尚未就绪，此时回传会被判为"答错"。

**② 延迟一小段再回调，模拟真实识别耗时**

```javascript
var d = 10 + Math.floor(Math.random() * 12);   // 10~21ms
setTimeout(function () {
  if (window[t]) { window[t](b64e([null, r])); }   // 回调 [null, 答案]
}, d);
```

### 6.4 加速切题（可选）

官方在判定答对后有 200ms 切题定时器，可压到 1ms：

```javascript
var __origST = window.setTimeout;
window.setTimeout = function (fn, ms) {
  if (ms === 200 && Date.now() < window.__pkFastUntil) { ms = 1; }
  return __origST.call(window, fn, ms);
};
```

同理，开场 ready-go 的 `2000/1000/500ms` 计时链也可压缩，并让 `HTMLMediaElement.prototype.play` 对 ready_go 资源直接 resolve 以静音跳过。

---

## 7. 答案卡构造与本地结果写入

见 `opensource/snippets/java/03_answer_card.java`。

### 7.1 JSON 结构

```jsonc
{
  "...examVO 原字段...": "...",
  "examVO": {
    "...examVO 原字段...": "...",
    "questions": [ /* 见下 */ ],
    "correctCnt": 20,
    "costTime": 1200,
    "updatedTime": 1750000000000
  },
  "userInfos": [],
  "costTime": 1200
}
```

### 7.2 每题字段

| 字段 | 值 | 含义 |
| --- | --- | --- |
| `userAnswer` | `q.optString("answer")` | 用户答案 = 正确答案 |
| `curTrueAnswer.answer` | `1` | 识别结果标记，1 = 判对 |
| `curTrueAnswer.recognizeResult` | 正确答案字符串 | 识别出的内容 |
| `curTrueAnswer.pathPoints` | `[]` | 笔迹点（由笔迹合成模块填充） |
| `status` | `1` | 1 = 正确 |

### 7.3 costTime 范围（重要）

```java
long cost = (capturedAt > 0) ? (System.currentTimeMillis() - capturedAt) : 8000;
cost = Math.max(2000, Math.min(cost, 9000));
```

> 实测约 **1.2~9 秒**可通过；过小或过大都会被拒。这里用真实经过时间并夹到 `[2000, 9000]`。

### 7.4 本地结果写入（重要坑）

前端存储约定是：

```javascript
localStorage["__local_" + key] = Base64.encode(json);
```

> ⚠️ 早期错写为 `localStorage['exerciseResult'] = 明文 JSON`，结果页按 `__local_exerciseResult` 读取 → 读不到 → 上报空结果，
> 表现为**"服务器已记账、前端却显示一道题没答"**。

---

## 8. 笔迹合成（决定能否过风控）

见 `opensource/snippets/js/05_stroke_sim.js`。仅劫持识别桥**不够**——服务端会记录笔迹轨迹。

### 8.1 形状库

归一化坐标（0~1）的字符笔画库 `S1`，覆盖 `< > 0-9 + - = × ÷` 等；未命中字符走兜底弧线 `FALLBACK`。

### 8.2 排布与抖动

```javascript
var cw = Math.min(.5, .72 / n);          // 按字符数分区
var x0 = .5 - (n * cw) / 2;
x: r.left + r.width  * (x0 + k*cw + p[0]*cw + (Math.random()*2-1)*.006)  // ±0.006 抖动
y: r.top  + r.height * (.3 + p[1]*.55 + (Math.random()*2-1)*.008)        // ±0.008 抖动
```

### 8.3 事件构造（重要坑）

目标使用 **signature_pad v5.0.4 且 `forceUseTouch: true`**：

> ⚠️ canvas 只监听 `mousedown` / `touchstart`，**不监听 pointer 事件**。
> ⚠️ `touchend` 必须 `touches = []` 且 `targetTouches = []`，否则不触发。

```javascript
var t = new Touch({ identifier: 1, target: el, clientX: x, clientY: y,
                    pageX: x, pageY: y, screenX: x, screenY: y,
                    radiusX: 6, radiusY: 6, force: .4 + Math.random()*.2 });  // 笔压随机

new TouchEvent(type, {
  bubbles: true, cancelable: true,
  touches:       last ? [] : [t],     // ★
  targetTouches: last ? [] : [t],     // ★
  changedTouches: [t]
});
```

### 8.4 分帧播放（时间戳必须真实）

```javascript
点间间隔：2 + floor(random()*3)   // 2~4ms
笔间间隔：6 + floor(random()*8)   // 6~13ms
```

### 8.5 实测经验（最关键的一节）

| 实验 | 整卷耗时 | 结果 |
| --- | --- | --- |
| 假笔迹（每题 5 点相同直线 + 时间戳全 0ms） | 3.3 秒 | ❌ 判风控，成绩清零 |
| 真实形状 + 真实分帧时间戳 + 坐标抖动 + 随机笔压 | **1.2 秒** | ✅ 全部通过 |
| 空笔迹（`script: null`） | — | ✅ 放行（但保留笔迹更稳妥） |

> **结论：风控看的是"像不像人写的"，不是绝对速度。**

---

## 9. DEX 注入与页面守卫

见 `opensource/snippets/java/01_attach.java`。在目标 `WebActivity.onCreate` 中插桩调用 `attach()`。

### 9.1 页面白名单

```java
private static final String PK_PAGE_KEY = "leo-web-oral-pk/";

boolean isMathPkPage(url) {
  if (url == null || !url.contains(PK_PAGE_KEY)) return false;
  // 英语页面位于同一个包内，需单独排除
  if (url.contains("english-words.html") || url.contains("english-word-match.html")) return false;
  return url.contains("exercise.html") || url.contains("pk.html");
}
```

### 9.2 取 WebView（含回退）

优先走官方同款路径，失败再退回 View 树 BFS 扫描：

```java
Object webApp = activity.getClass().getMethod("getWebApp").invoke(activity);
Object wv     = webApp.getClass().getMethod("getWebView").invoke(webApp);
// 失败 → findWebView(activity)：BFS 扫描 android.R.id.content
```

`evaluateJavascript` 的 `ValueCallback` 用**动态代理**接住返回值。

### 9.3 跨局状态复位

```java
if (url.contains("exercise.html")) {
  autoSubmitted = false; submitting = false; lastSubmittedPkId = null;
}
```

避免上一局状态串味。

### 9.4 悬浮按钮开关语义

- 未开 → 开启，文案 `已就绪·点此关闭`
- 已开 → 关闭并复位，文案 `1秒答题`

---

## 10. 加解密

| 操作 | 方法 | 说明 |
| --- | --- | --- |
| 加密答案卡 | `ds.i4.a.c(bytes)` | GZIP + 自反变换 |
| 解密题目 | `ds.i4.a.a(bytes)` | 自反变换 + GZIP（**与加密是同一系列函数**） |

自反变换意味着 `f(f(x)) == x`，加解密共用一套逻辑。

---

## 11. 复刻步骤（工具链与流程）

| 步骤 | 工具 | 产出 |
| --- | --- | --- |
| 1. 反编译 | jadx 1.5.6 | `decompiled/sources/`（Java）+ `decompiled/resources/` |
| 2. Native 分析 | IDA / Ghidra | 定位 `0x41A3E`、`0x44280` 等偏移 |
| 3. so patch | Python（`06_so_patch.py` 思路） | 去指纹校验的 `libRequestEncoder.so` |
| 4. DEX 注入 | apktool / smali | 插入 `PkHelper`（attach + 悬浮按钮） |
| 5. JS 注入 | WebView `evaluateJavascript` | 识别桥劫持 + 笔迹合成 |
| 6. 回编译 | apktool | 未签名 APK |
| 7. 对齐签名 | zipalign + apksigner（**自签证书**） | 成品 APK |
| 8. 验证 | adb + 真机 | 见 §13 |

> 无应用级签名校验，所以自签证书即可正常运行；但**改包签名与官方不同，无法覆盖安装**，必须先卸载官方版本。

---

## 12. 已知坑位清单

| # | 坑 | 后果 | 正确处理 |
| --- | --- | --- | --- |
| 1 | 只匹配 `/pk/match` | 8 人局抓不到题 | 同时匹配 `/multi/match` |
| 2 | 用 `AB64:` 前缀判定成功 | 匹配失败被误判成功 | base64 解码后判 `charAt(0) !== '{'` |
| 3 | 结果写入 `localStorage['exerciseResult']` | 服务器记账但前端显示 0 题 | 用 `localStorage["__local_" + key]` + Base64 |
| 4 | `expectedResult` 为空仍回 trigger | 被判答错 | 吞掉不回 |
| 5 | `touchend` 带 `touches` | signature_pad 不触发 | `touches = []`、`targetTouches = []` |
| 6 | 用 pointer 事件 | canvas 不监听 pointer | 用 touch 事件（`forceUseTouch: true`） |
| 7 | 笔迹时间戳全 0 / 形状固定 | 风控清零 | 真实形状 + 真实分帧 + 抖动 + 随机笔压 |
| 8 | `costTime` 超出范围 | 提交被拒 | 夹到 `[2000, 9000]` ms |
| 9 | patch 时 nop 掉 `0x41A48` | 真机 SIGSEGV | 只改 `0x41A3E` 起 10 字节 |
| 10 | 覆盖安装 | 签名冲突 | 先卸载官方版 |
| 11 | 一键登录 / QQ / 微信登录 | 服务端拒绝（签名校验） | **必须用短信验证码登录** |
| 12 | 进入对局后才开外挂 | 题目已加载完毕，无法触发 | 进对局页**之前**点开 |

---

## 13. 使用限制（服务端硬限制，无法绕过）

1. **必须用短信验证码登录**——一键登录 / QQ / 微信都会因改包签名被服务端拒绝。
2. **必须在进入对局页之前点开外挂**：进入 PK 选择页 → 点悬浮按钮开启 → 再进入对局。
3. **每账号约 60 秒 PK 匹配冷却**——打完立刻匹配会返回"请求过于频繁"（前端显示"现场太火爆"）。
4. **安装前必须卸载官方版本**。
5. **仅支持数学 PK**——语文（诗词/成语）与英语页面使用独立 H5，不生效。

---

## 14. 待自行验证项

1. `libRequestEncoder.so::zcvsd1wr2t` 的**具体签名算法**（当前结论为 md5 组合，已在真机 5/5 命中；但 T410 编码器内部细节需 IDA/Ghidra 进一步确认）。
2. `libdu.so` 内部是否含 root/模拟器环境检测字符串（strings 扫描未发现明显命中，但数盟 SDK 通常有环境采集逻辑）。
3. 上述坐标基于 **v52** 静态反编译结果，**跨版本可能因混淆改名**（`p005ds/c5`、`cq/o`、`br/d` 等）而失效，需按行为特征重新定位。

---

## 15. 声明

本报告仅用于**安全研究与攻防对抗评估**，对应"反外挂检测机制排查"的研究目标。将自动答题用于线上 PK 会直接损害真人玩家体验，由此产生的账号处罚与合规风险由使用者自行承担。详见 [DISCLAIMER.md](opensource/DISCLAIMER.md)。
