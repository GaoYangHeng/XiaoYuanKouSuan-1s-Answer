# 小猿口算 PK 自动答题 —— 逆向工程仓库

> 目标应用：`com.fenbi.android.leo`（v52 / 3.141.1）
> 完整逆向产物：反编译源码、Native 分析脚本、改包工程、成品 APK 与技术报告。

---

## 🚀 只想用效果？直接装改版 APK

**不想研究原理、只想拿到成品** —— 直接下载安装：

### [`release/xiaoyuan-kousuan-1s-answer-v52.apk`](release/xiaoyuan-kousuan-1s-answer-v52.apk)（约 82 MB）

```bash
adb uninstall com.fenbi.android.leo      # 先卸载官方版（签名不同，无法覆盖安装）
adb install -r release/xiaoyuan-kousuan-1s-answer-v52.apk
```

装完必读三条：

1. **必须用「短信验证码」登录**（一键登录 / QQ / 微信会因改包签名被服务端拒绝）
2. **进入对局页之前**先点悬浮按钮开启（先进对局再点，题目已加载完，不会触发）
3. 打完一局有**约 60 秒匹配冷却**，这是服务端硬限制

→ 完整使用说明见 [`opensource/README.md`](opensource/README.md)
→ 想搞懂原理自己复刻？直奔 **[`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md)**

---

## 一句话原理

**判题在客户端本地完成**：题目下发时正确答案已随题目一起到达，客户端只做「识别出的字符串」与「正确答案」的精确相等比对，无服务端二次判题。所以不需要骗过服务端，只需让"识别结果"等于"正确答案"。

---

## 实现原理图

```mermaid
flowchart TB
    subgraph BUILD["🔧 构建期（只需做一次）"]
        direction LR
        P1["① jadx 反编译<br/>decompiled/"] --> P2["② so patch<br/>去掉签名指纹校验"]
        P2 --> P3["③ DEX 注入<br/>PkHelper + 悬浮按钮"]
        P3 --> P4["④ 回编译 + 自签名"]
        P4 --> P5(["✅ 成品 APK<br/>release/"])
    end

    subgraph PLAY["🎮 运行期（每一局）"]
        direction TB
        A(["题目下发<br/>答案随题到达"]) --> B["① 拦截 XHR / fetch<br/>抓题目响应"]
        B --> C["② 解密题目<br/>ds.i4.a.a()"]
        C --> D["③ 合成笔迹<br/>像人写的轨迹"]
        D --> E["④ 劫持识别桥<br/>直接回传正确答案"]
        E --> F{"⑤ 本地判定<br/>Intrinsics.areEqual"}
        F -->|"识别结果 == 正确答案"| G["⑥ 构造答案卡<br/>userAnswer / status / costTime"]
        G --> H(["⑦ 提交成绩<br/>POST exercise/submit"])
    end

    SIGN["🔐 旁路：请求签名<br/>c5.c().b(path) → zcvsd1wr2t → libRequestEncoder.so"]
    BAD["❌ 不打 patch<br/>path 首字节被污染 → HTTP 417"]
    SIGN -.-> BAD
    SIGN -.->|"打过 patch"| H

    P5 ==> PLAY

    classDef key fill:#fff4d6,stroke:#e0a800,stroke-width:2px,color:#000
    classDef bad fill:#fde2e2,stroke:#c62828,stroke-width:2px,color:#000
    class P2,D,E key
    class BAD bad
```

> 🟡 **高亮的三步是成败关键**：so patch（否则 417）、笔迹合成（否则风控清零）、识别桥劫持（否则拿不到分）。

---

## 资产目录结构图

```mermaid
flowchart LR
    ROOT(("仓库根"))

    subgraph DOC["📄 文档 · 先看这里"]
        direction TB
        D1["README.md<br/>本页"]
        D2["TECHNICAL_REPORT.md<br/>⭐ 技术报告（515 行）"]
        D3["reports/<br/>攻击面 + 关联关系分析"]
        D4["opensource/README.md<br/>成品使用说明"]
        D5["opensource/DISCLAIMER.md<br/>免责声明"]
    end

    subgraph RE["🔍 逆向产物"]
        direction TB
        R1["decompiled/<br/>jadx 源码 + 资源<br/>29362 个类"]
        R2["so_dump/<br/>Native 转储"]
        R3["apk/<br/>原始 APK ⚠️ 未入库"]
    end

    subgraph SC["🛠 分析脚本"]
        direction TB
        S1["disasm_*.py<br/>Native 反汇编"]
        S2["find_*.py / dump_*.py<br/>定位与转储"]
        S3["crack_sign*/<br/>签名破解"]
        S4["elf_*.py / extract_*.py<br/>ELF 与字符提取"]
    end

    subgraph BP["🧩 改包工程"]
        direction TB
        B1["mod_apk/<br/>smali 工程（work/ 未入库）"]
        B2["opensource/snippets/<br/>7 个关键片段"]
    end

    subgraph OUT["📦 成品"]
        direction TB
        O1["release/<br/>v52 APK"]
    end

    ROOT --> DOC
    ROOT --> RE
    ROOT --> SC
    ROOT --> BP
    ROOT --> OUT
```

> ⚠️ `decompiled/`、`apk/`、`mitmconf/`、`mod_apk/work/` 被 `.gitignore` 排除，不入版本库；反编译产物已单独打包为 zip 分发，仓库内不可见。

---

## 反外挂强度速览

```mermaid
flowchart LR
    subgraph NONE["🟢 无 —— 无需处理"]
        direction TB
        N1["加固 / 加壳"]
        N2["Java 层签名校验"]
        N3["反调试"]
        N4["Xposed / Frida 检测"]
        N5["模拟器检测"]
    end

    subgraph WEAK["🟡 弱 —— 可忽略"]
        direction TB
        W1["root 检测<br/>仅崩溃日志标记"]
    end

    subgraph MID["🔴 中 —— 需处理"]
        direction TB
        M1["Native 签名校验<br/>→ 打 so patch"]
        M2["时间对齐 / 防重放<br/>→ 保持系统时间准确"]
        M3["设备指纹风控<br/>→ 上报默认关闭"]
    end
```

逐项证据见 [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md) 第 1 节。

---

## 声明

本项目为**安全研究与教育用途**的逆向工程笔记。PK 对局中有真人玩家，自动化会直接损害他人体验，请勿用于线上对局。

完整声明见 [`opensource/DISCLAIMER.md`](opensource/DISCLAIMER.md)。
