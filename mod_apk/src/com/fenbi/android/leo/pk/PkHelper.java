package com.fenbi.android.leo.pk;

import android.app.Activity;
import android.content.ClipboardManager;
import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.widget.Toast;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import okhttp3.ResponseBody;
import org.json.JSONObject;

/**
 * 改包入口：在 SimpleWebAppFireworkActivity 里调用 attach()，
 * 判断是否为比大小 PK 页（URL 含 leo-web-oral-pk/pk.html），挂载悬浮按钮。
 * interceptResponse() 被 cq/v 拦截器调用，拦截 match/v2 响应缓存答案。
 */
public class PkHelper {

    private static final String PK_PAGE_KEY = "leo-web-oral-pk/";
    private static final String MATCH_KEY = "/pk/match";
    private static final String SUBMIT_PATH = "/leo-game-pk/android/math/pk/submit";

    private static PkFloatButton button;
    /**
     * 所有已创建的悬浮按钮。每个页面 attach 都会新建一个，若只更新静态 button，
     * 会出现"用户在 A 页面点按钮、代码却更新了 B 页面按钮"→ 看起来点了没反应。
     * 因此状态变化时必须遍历更新全部按钮。
     */
    private static final java.util.List<PkFloatButton> buttons =
            new java.util.ArrayList<PkFloatButton>();
    private static final PkAnswerEngine engine = new PkAnswerEngine();
    private static String lastMatchUrl;
    private static volatile String lastLocation = "";
    /** 最近一次轮询上报的已答题数（来自 JS "P ... r=N"），用于判断对局是否真的开始 */
    private static volatile int lastRecvCount = 0;
    /** 匹配失败重试次数，用于在横条上反馈"还在重试" */
    private static volatile int retryCount = 0;
    private static volatile String lastError = "";
    private static final Handler main = new Handler(Looper.getMainLooper());
    /** 全局上下文，用于页面销毁后仍能弹出提示 */
    private static Context appContext;

    /**
     * 全量抓包落盘：把每一个 leo 域名请求/响应逐行追加到 app 私有文件，
     * 路径 /sdcard/Android/data/com.fenbi.android.leo/files/pk_capture.log（无需存储权限）。
     * 跑完一局后 adb pull 该文件即可拿到完整交互记录。
     */
    private static BufferedWriter capW;
    private static final String CAP_TAG = "PKCAP:";

    private static synchronized void capture(String line) {
        try {
            if (capW == null && appContext != null) {
                File dir = appContext.getExternalFilesDir(null);
                if (dir == null) {
                    dir = appContext.getFilesDir();
                }
                File f = new File(dir, "pk_capture.log");
                capW = new BufferedWriter(new FileWriter(f, true));
            }
            if (capW != null) {
                String ts = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(new Date());
                capW.write(CAP_TAG + ts + " | " + line + "\n");
                capW.flush();
            }
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "capture err " + t);
        }
    }

    /**
     * 只在数学 PK 的两个页面生效：PK 选择页(pk.html) 与数学对局页(exercise.html)。
     * 明确排除：
     *  - 语文 leo-web-poem-pk（玩法不同，实测点开始 PK 会报"人太多了"并被踢出）
     *  - 英语 english-words.html / english-word-match.html（同在 oral-pk 包下，需单独排除）
     *  - 结果页 result.html（答完不需要外挂按钮，避免残留"自动中"字样）
     */
    private static boolean isMathPkPage(String url) {
        if (url == null || !url.contains(PK_PAGE_KEY)) {
            return false;
        }
        if (url.contains("english-words.html") || url.contains("english-word-match.html")) {
            return false;
        }
        return url.contains("exercise.html") || url.contains("pk.html");
    }

    public static void attach(final Activity activity) {
        try {
            appContext = activity.getApplicationContext();
            final String url = extractUrl(activity);
            android.util.Log.i("PkHelper", "attach url=" + url);
            if (!isMathPkPage(url)) {
                return;
            }
            button = new PkFloatButton(activity, new Runnable() {
                @Override
                public void run() {
                    handleMainClick(activity);
                }
            }, new Runnable() {
                @Override
                public void run() {
                    PkSettingsDialog.show(activity);
                }
            });
            // 登记到按钮列表，供 setStatus 全量刷新（上限放宽，避免老页面按钮被挤出列表后文案不更新）
            while (buttons.size() > 12) {
                buttons.remove(0);
            }
            buttons.add(button);
            button.setOnRetryCancel(new Runnable() {
                @Override
                public void run() {
                    stopRetryLoop();
                    showRetryBar(false, null);
                    retryCount = 0;
                    toast(activity, "已取消重试");
                }
            });
            main.post(new Runnable() {
                @Override
                public void run() {
                    try {
                        button.show();
                        android.util.Log.i("PkHelper", "button shown on " + activity.getClass().getSimpleName());
                    } catch (Throwable t) {
                        lastError = "显示悬浮按钮失败: " + stack(t);
                        android.util.Log.i("PkHelper", "show err " + t);
                    }
                }
            });
            if (url.contains("exercise.html")) {
                // 进入新对局：必须清掉上一局的提交标志。
                // 否则 autoSubmitted/submitting 残留会让 onCaptured 开头直接 return，
                // 表现为"在 PK 页开了外挂，进对局却莫名其妙不答题，像被关掉了"。
                autoSubmitted = false;
                submitting = false;
                lastSubmittedPkId = null;
                lastRecvCount = 0;
                android.util.Log.i("PkHelper", "enter exercise, reset submit flags state=" + state);
                // 注：原先这里有"N 秒没答到题就自动关闭"的看门狗，按用户要求已移除 ——
                // 现在逻辑稳定，被限流时用户可在主页手动关闭，自动关闭反而会误杀 8 人局（凑人慢）。
            }
            if (state == ST_ARMED && url != null && url.contains("exercise.html")) {
                setStatus(activity, "自动中·点此关闭", "");
                engine.onExamCaptured = new Runnable() {
                    @Override
                    public void run() {
                        onCaptured(activity);
                    }
                };
            } else if (state == ST_ARMED && url != null && url.contains("pk.html")) {
                setStatus(activity, "已就绪·点此关闭", "");
            } else if (state == ST_IDLE && url != null
                    && (url.contains("exercise.html") || url.contains("pk.html"))
                    && PkSettings.getAutoArm(activity)) {
                // 设置项「自动开启」：进入 PK 页免点按钮直接武装
                state = ST_ARMED;
                autoSubmitted = false;
                submitting = false;
                engine.onExamCaptured = new Runnable() {
                    @Override
                    public void run() {
                        onCaptured(activity);
                    }
                };
                setStatus(activity, url.contains("exercise.html") ? "自动中·点此关闭" : "已就绪·点此关闭", "");
                android.util.Log.i("PkHelper", "auto-armed by settings");
            }
            installHook(activity);
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "attach err " + t);
        }
    }

    private static String extractUrl(Activity activity) {
        try {
            android.content.Intent it = activity.getIntent();
            if (it == null) {
                return null;
            }
            String u = it.getStringExtra("url");
            if (u == null) {
                u = it.getStringExtra("pagePath");
            }
            if (u == null) {
                u = it.getStringExtra("path");
            }
            if (u == null) {
                u = it.getDataString();
            }
            if (u == null && it.getExtras() != null) {
                for (String k : it.getExtras().keySet()) {
                    Object v = it.getExtras().get(k);
                    if (v instanceof String && ((String) v).contains("pk.html")) {
                        android.util.Log.i("PkHelper", "attach hit extra key=" + k);
                        return (String) v;
                    }
                }
            }
            return u;
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "extractUrl err " + t);
            return null;
        }
    }

    private static final String AUTO_ANSWER_JS =
            "if (!window.__pkAuto) { window.__pkAuto = 1; (function () { function b64d(s) { var b = atob(" 
                    + "s), u = new Uint8Array(b.length), i; for (i = 0; i < b.length; i++) { u[i] = b.charCodeAt(i)" 
                    + "; } return JSON.parse(new TextDecoder().decode(u)); } function b64e(o) { var b = new TextEnc" 
                    + "oder().encode(JSON.stringify(o)), s = '', i; for (i = 0; i < b.length; i++) { s += String.fr" 
                    + "omCharCode(b[i]); } return btoa(s); } function log(m) { try { if (window.PkHook && PkHook.pk" 
                    + "Log) { PkHook.pkLog(m); } } catch (e) { } } window.__pkRecv = 0; window.__pkBusy = 0; window" 
                    + ".__pkDraw = 0; window.__pkMode = 1; window.__pkSwallow = 0; window.__pkInjectT = Date.now();" 
                    + " window.__pkEarlyUntil = Date.now() + 5000; var __origST = window.setTimeout; window.setTime" 
                    + "out = function (fn, ms) { try { /* ready-go 计时链（2000/1000/500ms）：进入对局 5s 内一律压成 1ms，不再受 __pkR" 
                    + "ecv 影响 */ if ((ms === 2000 || ms === 1000 || ms === 500) && Date.now() < (window.__pkEarlyUn" 
                    + "til || 0)) { ms = 1; } if (ms === 200 && Date.now() < (window.__pkFastUntil || 0)) { ms = 1;" 
                    + " } } catch (e) { } return __origST.call(window, fn, ms); }; /* ready-go 音频静音跳过：play 时若资源是 re" 
                    + "ady_go，直接完成不发声 */ try { var __origPlay = HTMLMediaElement.prototype.play; HTMLMediaElement.p" 
                    + "rototype.play = function () { try { if (this.src && this.src.indexOf('ready_go') >= 0) { thi" 
                    + "s.pause(); return Promise.resolve(); } } catch (e) { } return __origPlay.apply(this, argumen" 
                    + "ts); }; } catch (e) { } window.MathExerciseWebView = { recognize: function (p) { try { var a" 
                    + " = (b64d(p).arguments || [])[0] || {}; var ans = a.expectedResult || []; var t = a.trigger; " 
                    + "if (!t || !ans.length) { window.__pkSwallow += 1; log('swallow #' + window.__pkSwallow + ' a" 
                    + "ns=' + JSON.stringify(ans)); return true; } var r = String(ans[0]); window.__pkRecv += 1; wi" 
                    + "ndow.__pkCurAns = r; window.__pkLastRecv = Date.now(); window.__pkFastUntil = Date.now() + 4" 
                    + "00; log('recognize #' + window.__pkRecv + ' ans=' + JSON.stringify(ans) + ' ret=' + r); var " 
                    + "d = (window.__pkDelay || 12) + Math.floor(Math.random() * (window.__pkJit || 12)); setTimeout(function () { try { if (window[t]) { win" 
                    + "dow[t](b64e([null, r])); } } catch (e) { log('cb err ' + e); } }, d); return true; } catch (" 
                    + "e) { log('rec err ' + e); return true; } } }; var S1 = { '<': [[[.62, .32], [.5, .43], [.38," 
                    + " .5], [.5, .58], [.61, .68]]], '>': [[[.38, .32], [.5, .43], [.62, .5], [.5, .58], [.39, .68" 
                    + "]]], '0': [[[.44, .32], [.35, .4], [.35, .6], [.44, .68], [.56, .68], [.65, .6], [.65, .4], " 
                    + "[.56, .32], [.44, .32]]], '1': [[[.44, .37], [.53, .3], [.53, .68]]], '2': [[[.36, .38], [.4" 
                    + "7, .3], [.6, .34], [.56, .47], [.38, .62], [.36, .68], [.63, .68]]], '3': [[[.36, .33], [.57" 
                    + ", .32], [.45, .46], [.58, .52], [.56, .63], [.44, .68], [.34, .64]]], '4': [[[.57, .3], [.37" 
                    + ", .55], [.65, .55]]], '5': [[[.59, .31], [.4, .31], [.38, .46], [.53, .45], [.62, .55], [.54" 
                    + ", .67], [.4, .66]]], '6': [[[.57, .32], [.42, .5], [.4, .63], [.51, .68], [.6, .61], [.57, ." 
                    + "52], [.44, .51]]], '7': [[[.36, .32], [.62, .32], [.46, .68]]], '8': [[[.5, .32], [.41, .37]" 
                    + ", [.47, .47], [.56, .53], [.6, .62], [.51, .68], [.42, .62], [.46, .53], [.55, .46], [.6, .3" 
                    + "8], [.5, .32]]], '9': [[[.6, .44], [.45, .42], [.4, .34], [.55, .3], [.62, .41], [.58, .66]]" 
                    + "], '+': [[[.5, .32], [.5, .66]], [[.33, .49], [.67, .49]]], '-': [[[.34, .5], [.66, .5]]], '" 
                    + "=': [[[.32, .42], [.68, .42]], [[.32, .6], [.68, .6]]], '×': [[[.36, .36], [.64, .64]], [[.6" 
                    + "4, .36], [.36, .64]]], 'x': [[[.36, .36], [.64, .64]], [[.64, .36], [.36, .64]]], '*': [[[.5" 
                    + ", .34], [.5, .64]], [[.36, .42], [.64, .42]], [[.4, .6], [.6, .6]]], '÷': [[[.32, .5], [.68," 
                    + " .5]], [[.5, .35], [.5, .37]], [[.5, .63], [.5, .65]]], '/': [[[.62, .3], [.38, .7]]], ':': " 
                    + "[[[.5, .4], [.5, .41]], [[.5, .6], [.5, .61]]] }; var FALLBACK = [[[.38, .58], [.44, .36], [" 
                    + ".54, .38], [.58, .54], [.5, .66], [.42, .62]]]; function charStrokes(ch) { return S1[ch] || " 
                    + "FALLBACK; } function jitter(v, amp) { return v + (Math.random() * 2 - 1) * amp; } function b" 
                    + "uildStrokes(ans, r) { var HF = window.__pkHuman ? (0.4 + (window.__pkInt || 50) / 100 * 1.2) : 0; var chars = String(ans).split(''); if (!chars.length) { chars = ['?'];" 
                    + " } var n = chars.length; var cw = Math.min(.5, .72 / n); var x0 = .5 - (n * cw) / 2; var out" 
                    + " = [], k, ch, st, i, j, p, nx, ny; for (k = 0; k < n; k++) { ch = chars[k]; st = charStrokes" 
                    + "(ch); for (i = 0; i < st.length; i++) { var pts = []; for (j = 0; j < st[i].length; j++) { p" 
                    + " = st[i][j]; nx = x0 + k * cw + p[0] * cw; ny = .3 + p[1] * .55; pts.push({ x: r.left + r.wi" 
                    + "dth * jitter(nx, .006 * HF), y: r.top + r.height * jitter(ny, .008 * HF) }); } out.push(pts); } } retu" 
                    + "rn out; } function padCanvas() { var l = document.querySelectorAll('canvas'), pads = [], oth" 
                    + "ers = [], i, c, r, ta; for (i = 0; i < l.length; i++) { c = l[i]; r = c.getBoundingClientRec" 
                    + "t(); if (r.width < 100 || r.height < 50) { continue; } ta = (c.style && c.style.touchAction)" 
                    + " ? c.style.touchAction : ''; if (ta === 'none') { pads.push({ el: c, r: r }); } else { other" 
                    + "s.push({ el: c, r: r }); } } if (pads.length) { return pads[0]; } others.sort(function (a, b" 
                    + ") { return b.r.width * b.r.height - a.r.width * a.r.height; }); return others[0] || null; } " 
                    + "function mev(type, x, y, buttons) { var e; try { e = new MouseEvent(type, { bubbles: true, c" 
                    + "ancelable: true, view: window, clientX: x, clientY: y, screenX: x, screenY: y, button: 0, bu" 
                    + "ttons: buttons, detail: 0 }); } catch (err) { e = document.createEvent('MouseEvents'); e.ini" 
                    + "tMouseEvent(type, true, true, window, 0, x, y, x, y, false, false, false, false, 0, null); }" 
                    + " return e; } function mkTouch(el, x, y) { if (typeof Touch === 'function') { try { return ne" 
                    + "w Touch({ identifier: 1, target: el, clientX: x, clientY: y, pageX: x, pageY: y, screenX: x," 
                    + " screenY: y, radiusX: 6, radiusY: 6, force: .4 + Math.random() * .2 }); } catch (e) { } } re" 
                    + "turn { identifier: 1, target: el, clientX: x, clientY: y, pageX: x, pageY: y, screenX: x, sc" 
                    + "reenY: y, force: .5 }; } function tev(el, type, x, y) { var t = mkTouch(el, x, y); var last " 
                    + "= (type === 'touchend'); var ini = { bubbles: true, cancelable: true, touches: last ? [] : [" 
                    + "t], targetTouches: last ? [] : [t], changedTouches: [t] }; var e; try { e = new TouchEvent(t" 
                    + "ype, ini); } catch (err) { e = document.createEvent('Event'); e.initEvent(type, true, true);" 
                    + " e.touches = ini.touches; e.targetTouches = ini.targetTouches; e.changedTouches = ini.change" 
                    + "dTouches; } return e; } function down(c, x, y) { if (window.__pkMode === 1) { c.dispatchEven" 
                    + "t(tev(c, 'touchstart', x, y)); } else { c.dispatchEvent(mev('mousedown', x, y, 1)); } } func" 
                    + "tion move(c, x, y) { if (window.__pkMode === 1) { c.dispatchEvent(tev(c, 'touchmove', x, y))" 
                    + "; } else { c.dispatchEvent(mev('mousemove', x, y, 1)); } } function up(c, x, y) { if (window" 
                    + ".__pkMode === 1) { c.dispatchEvent(tev(c, 'touchend', x, y)); } else { c.dispatchEvent(mev('" 
                    + "mouseup', x, y, 0)); } } function write(ans, done) { var pad = padCanvas(); if (!pad) { done" 
                    + "(); return; } var strokes = buildStrokes(ans, pad.r); var si = 0, aborted = false, finished " 
                    + "= false; var guard = setTimeout(function () { aborted = true; if (!finished) { finished = tr" 
                    + "ue; done(); } }, 4000); function nextStroke() { if (aborted) { return; } if (si >= strokes.l" 
                    + "ength) { clearTimeout(guard); if (!finished) { finished = true; done(); } return; } var pts " 
                    + "= strokes[si]; si += 1; down(pad.el, pts[0].x, pts[0].y); var i = 1; (function step() { if (" 
                    + "aborted) { return; } if (i < pts.length) { move(pad.el, pts[i].x, pts[i].y); i += 1; setTime" 
                    + "out(step, window.__pkHuman ? 2 + Math.floor(Math.random() * 3) : 1); } else { up(pad.el, pts[i - 1].x, pts[i - 1].y" 
                    + "); setTimeout(nextStroke, window.__pkHuman ? 6 + Math.floor(Math.random() * 8) : 1); } })(); } nextStroke(); } wind" 
                    + "ow.__pkWrite = write; window.__pkAutoStart = function (iv, max) { var n = 0; window.__pkRecv" 
                    + " = 0; window.__pkBusy = 0; window.__pkDraw = 0; window.__pkMode = 1; window.__pkSwallow = 0;" 
                    + " window.__pkStartT = Date.now(); window.__pkModeT = 0; if (window.__pkTimer) { clearInterval" 
                    + "(window.__pkTimer); } window.__pkTimer = setInterval(function () { if (window.__pkBusy) { re" 
                    + "turn; } var now = Date.now(); if (n >= max * 3) { clearInterval(window.__pkTimer); window.__" 
                    + "pkTimer = null; return; } if (window.__pkRecv > 0 && now - (window.__pkLastRecv || 0) < 60) " 
                    + "{ return; } if (window.__pkRecv === 0 && window.__pkSwallow > 0 && now - (window.__pkLastTry" 
                    + " || 0) < 900) { return; } window.__pkLastTry = now; if (window.__pkRecv === 0 && window.__pk" 
                    + "Swallow === 0 && now - (window.__pkModeT || window.__pkStartT) > 2500) { window.__pkModeT = " 
                    + "now; window.__pkMode = window.__pkMode === 1 ? 0 : 1; log('no bridge traffic, switch mode=' " 
                    + "+ window.__pkMode); } n += 1; window.__pkBusy = 1; var ans = (n === 1) ? '' : (window.__pkCu" 
                    + "rAns || ''); window.__pkDraw += 1; write(ans, function () { setTimeout(function () { window." 
                    + "__pkBusy = 0; }, 25 + Math.floor(Math.random() * 25)); }); log('write #' + n + ' mode=' + wi" 
                    + "ndow.__pkMode); }, iv); return 'ok'; }; })(); }";
    private static final String HOOK_JS =
            "if (!window.__pkHook) { window.__pkHook = 1; (function () { var s = function (t) { try { window.__pkMatchData " +
                    "= t; var ok=false; if (t) { var ss=String(t); if (ss.indexOf('AB64:')===0) { try { var raw=atob(ss.substri" +
                    "ng(5)); ok=(raw.charAt(0)!=='{'); } catch (e3) { ok=true; } } else { ok=(ss.indexOf('examVO')>=0 || ss.i" +
                    "ndexOf('pkIdStr')>=0); } } try { if (window.PkHook) { if (ok) { PkHook.pkMatchOk(); } else { PkHook.pkMat" +
                    "chFailed(String(t).substring(0,150)); } } } catch (e2) { } if (window.PkHook) { PkHook.pkMatchCaptured(t)" +
                    "; } } catch (e) { } }; var o = XMLHttpRequest.prototype.ope" +
                    "n, f0 = XMLHttpRequest.prototype.send; XMLHttpRequest.prototype.open = function (m, u) { this.__u = u; return " +
                    "o.apply(this, arguments); }; XMLHttpRequest.prototype.send = function () { var x = this; x.addEventListener('l" +
                    "oad', function () { try { if (x.__u && (x.__u.indexOf('/pk/match') >= 0 || x.__u.indexOf('/multi/match') >= 0)) { var t = null; if (x.responseTyp" +
                    "e === 'arraybuffer' && x.response) { var u = new Uint8Array(x.response), b = ''; for (var k = 0; k < u.length;" +
                    " k++) { b += String.fromCharCode(u[k]); } t = 'AB64:' + btoa(b); } else if (x.responseType === '' || x.respons" +
                    "eType === 'text') { t = x.responseText; } else if (typeof x.response === 'string') { t = x.response; } else if" +
                    " (x.response) { t = JSON.stringify(x.response); } if (t) { s(t); } } } catch (e) { } }); return f0.apply(this," +
                    " arguments); }; var f = window.fetch; if (f) { window.fetch = function () { var u = (typeof arguments[0] === '" +
                    "string') ? arguments[0] : ((arguments[0] && arguments[0].url) || ''); var p = f.apply(this, arguments); try { " +
                    "if (u && (u.indexOf('/pk/match') >= 0 || u.indexOf('/multi/match') >= 0)) { p.then(function (r) { try { var ct = (r.headers.get('content-type" +
                    "') || ''); if (ct.indexOf('json') >= 0 || ct.indexOf('text') >= 0) { r.clone().text().then(function (t) { s(t)" +
                    "; }).catch(function () { }); } else { r.clone().arrayBuffer().then(function (b) { var u2 = new Uint8Array(b), " +
                    "str = ''; for (var k = 0; k < u2.length; k++) { str += String.fromCharCode(u2[k]); } s('AB64:' + btoa(str)); }" +
                    ").catch(function () { }); } } catch (e) { } }); } } catch (e) { } return p; }; window.__pkRetryMatch = " +
            "function () { try { if (document.readyState !== 'complete') { return 'loading'; } var els = document.querySelect" +
            "orAll('button,div,span,a'); for (var i = 0; i < els.length; i" +
            "++) { var el = els[i]; var tx = ((el.innerText || el.textContent || '') + ''); tx = tx.trim ? tx.trim() : tx; if" +
            " (tx.length > 0 && tx.length < 14 && (tx.indexOf('重试') >= 0 || tx.indexOf('再试') >= 0 || tx.indexOf('重新') " +
            ">= 0)) { el.click(); return 'clicked:' + tx; } } } catch (e) { return 'err:' + e; } try { location.reload(); retu" +
            "rn 'reload'; } catch (e2) { return 'reloaderr:' + e2; } }; } })(); }";

    /**
     * 全量请求捕获：hook 网页里所有 XHR / fetch，把发出去的全部请求上报到 logcat。
     *  - 非匹配请求只打一行（REQ1 XHR/FETCH method url）
     *  - 匹配/pk 相关请求打完整信息（REQFULL + REQH 全部请求头 + REQBODY）
     * match/v2 由网页 JS 发出、不经过 OkHttp 拦截器，只有这个 JS 层 hook 能看到它。
     * 通过 PkBridge.pkLog 上抛 → native Log.i("PkHelper","JS ...")。
     * 链式包装（保存注入时刻的 prototype 原方法），与 HOOK_JS 可叠加共存。
     */
    private static final String REQ_JS =
            "if(!window.__pkReqCap){window.__pkReqCap=1;(function(){"
                    + "function log(m){try{if(window.PkHook&&PkHook.pkLog){PkHook.pkLog(m);}}catch(e){}}"
                    + "function isPk(u){return !!u&&(u.indexOf('/match')>=0||u.indexOf('leo-game-pk')>=0||u.indexOf('/pk/')>=0);}"
                    + "var op=XMLHttpRequest.prototype.open,sr=XMLHttpRequest.prototype.setRequestHeader,sd=XMLHttpRequest.prototype.send;"
                    + "XMLHttpRequest.prototype.open=function(m,u){try{this.__c={m:m,u:u,h:{}};}catch(e){}return op.apply(this,arguments);};"
                    + "XMLHttpRequest.prototype.setRequestHeader=function(k,v){try{if(this.__c){this.__c.h[k]=v;}}catch(e){}return sr.apply(this,arguments);};"
                    + "XMLHttpRequest.prototype.send=function(b){var x=this;try{if(x.__c){var c=x.__c,pk=isPk(c.u);"
                    + "log((pk?'REQFULL ':'REQ1 ')+'XHR '+c.m+' '+c.u);if(pk){try{log('REQH '+JSON.stringify(c.h));}catch(e){}if(b){try{var bl=(b.byteLength!==undefined)?b.byteLength:-1;log('REQBODY '+(typeof b==='string'?b.substring(0,1500):'['+Object.prototype.toString.call(b)+' len='+bl+']'));}catch(e){}}}}"
                    + "}catch(e){}return sd.apply(this,arguments);};"
                    + "var f=window.fetch;if(f){window.fetch=function(){var a=arguments,u=(typeof a[0]==='string')?a[0]:((a[0]&&a[0].url)||''),i=a[1]||{};try{var pk=isPk(u),hd={};"
                    + "try{if(window.Headers&&i.headers&&typeof i.headers.forEach==='function'){i.headers.forEach(function(v,k){hd[k]=v;});}else if(i.headers){hd=i.headers;}}catch(e){}"
                    + "var bd=(typeof i.body==='string')?i.body:'';if(!bd&&i.body){try{bd='['+Object.prototype.toString.call(i.body)+']';}catch(e){bd='[?]';}}"
                    + "log((pk?'REQFULL ':'REQ1 ')+'FETCH '+(i.method||'GET')+' '+u);if(pk){try{log('REQH '+JSON.stringify(hd));}catch(e){}if(bd){try{log('REQBODY '+bd.substring(0,1500));}catch(e){}}}}catch(e){}return f.apply(this,a);};}"
                    + "log('REQCAP ok');"
                    + "try{log('REQCOOKIE '+document.cookie);}catch(e){try{log('REQCOOKIE ERR '+e);}catch(_e){}}"
                    + "try{var _l1='';for(var _i1=0;_i1<localStorage.length;_i1++){var _k1=localStorage.key(_i1);_l1+='|'+_k1+'='+localStorage.getItem(_k1);}log('REQLS '+_l1);}catch(e){try{log('REQLS ERR '+e);}catch(_e){}}"
                    + "try{var _l2='';for(var _i2=0;_i2<sessionStorage.length;_i2++){var _k2=sessionStorage.key(_i2);_l2+='|'+_k2+'='+sessionStorage.getItem(_k2);}log('REQSS '+_l2);}catch(e){try{log('REQSS ERR '+e);}catch(_e){}}"
                    + "})();}";

    private static void installHook(final Activity activity) {
        // 立即首查（attach 时 super.onCreate 未完成，主队列 post(0) 会在其完成后执行），100ms 级重试抢在 match 前
        main.post(new Runnable() {
            private int tries;

            @Override
            public void run() {
                try {
                    final Object x5 = getX5WebView(activity);
                    if (x5 == null) {
                        if (tries++ < 20) {
                            main.postDelayed(this, 100);
                        } else {
                            android.util.Log.i("PkHelper", "hook webview not found");
                        }
                        return;
                    }
                    android.util.Log.i("PkHelper", "hook target " + x5.getClass().getName());
                    currentWebView = x5;
                    try {
                        x5.getClass().getMethod("addJavascriptInterface", Object.class, String.class)
                                .invoke(x5, bridgeObj(), "PkHook");
                        android.util.Log.i("PkHelper", "bridge installed");
                    } catch (Throwable t) {
                        android.util.Log.i("PkHelper", "bridge err " + t);
                    }
                    startLoops(x5);
                    installReqCap(x5);
                } catch (Throwable t) {
                    android.util.Log.i("PkHelper", "installHook err " + t);
                }
            }
        });
    }

    /**
     * 全量请求捕获注入：与 ARM 状态无关，进入 PK 页即反复注入 REQ_JS。
     * 必须在 match 请求发出前挂上 hook；页面可能重载，故重试注入一段时间兜底。
     */
    private static void installReqCap(final Object x5) {
        final int[] n = {0};
        final Runnable[] r = new Runnable[1];
        r[0] = new Runnable() {
            @Override
            public void run() {
                try {
                    evalJs(x5, REQ_JS, false);
                } catch (Throwable t) {
                    android.util.Log.i("PkHelper", "reqcap err " + t);
                }
                if (n[0]++ < 15) {
                    main.postDelayed(r[0], 300);
                }
            }
        };
        main.post(r[0]);
    }

    public static class PkBridge {
        @JavascriptInterface
        public void pkMatchCaptured(final String body) {
            android.util.Log.i("PkHelper", "HOOK captured len=" + (body == null ? -1 : body.length()));
            new Thread(new Runnable() {
                @Override
                public void run() {
                    engine.parseCaptured(body);
                }
            }, "pk-hook-parse").start();
        }

        @JavascriptInterface
        public void pkMatchFailed(final String msg) {
            android.util.Log.i("PkHelper", "JS matchFailed " + msg);
            main.post(new Runnable() {
                @Override
                public void run() {
                    showRetryBar(true, "匹配失败，正在重试…");
                    startRetryLoop();
                }
            });
        }

        @JavascriptInterface
        public void pkMatchOk() {
            android.util.Log.i("PkHelper", "JS matchOk");
            main.post(new Runnable() {
                @Override
                public void run() {
                    stopRetryLoop();
                    showRetryBar(false, null);
                    retryCount = 0;
                }
            });
        }

        @JavascriptInterface
        public void pkLog(final String msg) {
            android.util.Log.i("PkHelper", "JS " + msg);
            capture("JS " + msg);
            if (msg != null && msg.startsWith("LOC ")) {
                lastLocation = msg.substring(4);
            }
            // 解析进度上报 "P d=.. r=.. s=.."，取已答题数 r=
            if (msg != null && msg.startsWith("P ")) {
                int i = msg.indexOf(" r=");
                if (i >= 0) {
                    try {
                        lastRecvCount = Integer.parseInt(msg.substring(i + 3).trim().split(" ")[0]);
                    } catch (Throwable ignore) {
                    }
                }
            }
        }
    }

    private static Object bridgeObj() {
        return new PkBridge();
    }

    /**
     * 优先走官方同款路径：activity.getWebApp().getWebView()（X5 真身），失败再退回 View 树扫描。
     */
    private static Object getX5WebView(Activity activity) {
        try {
            Object webApp = activity.getClass().getMethod("getWebApp").invoke(activity);
            if (webApp != null) {
                Object wv = webApp.getClass().getMethod("getWebView").invoke(webApp);
                if (wv != null) {
                    return wv;
                }
            }
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "getWebApp path err " + t);
        }
        return findWebView(activity);
    }

    private static void evalJs(Object x5, String js, final boolean readResult) {
        try {
            for (java.lang.reflect.Method m : x5.getClass().getMethods()) {
                if ("evaluateJavascript".equals(m.getName()) && m.getParameterTypes().length == 2
                        && m.getParameterTypes()[0] == String.class) {
                    Object cb = null;
                    try {
                        final Class<?> p1 = m.getParameterTypes()[1];
                        if (p1.isInterface()) {
                            cb = java.lang.reflect.Proxy.newProxyInstance(x5.getClass().getClassLoader(),
                                    new Class<?>[]{p1}, new java.lang.reflect.InvocationHandler() {
                                        @Override
                                        public Object invoke(Object proxy, java.lang.reflect.Method m2, Object[] a) {
                                            if (readResult && a != null && a.length > 0 && a[0] != null) {
                                                final String s = a[0].toString();
                                                android.util.Log.i("PkHelper", "pollResult " + s.substring(0, Math.min(120, s.length())));
                                                if (s.length() > 4 && !s.equals("null")) {
                                                    new Thread(new Runnable() {
                                                        @Override
                                                        public void run() {
                                                            try {
                                                                String real = new org.json.JSONTokener(s).nextValue().toString();
                                                                if (real.length() > 10) {
                                                                    engine.parseCaptured(real);
                                                                }
                                                            } catch (Throwable t2) {
                                                                android.util.Log.i("PkHelper", "poll parse err " + t2);
                                                            }
                                                        }
                                                    }, "pk-poll-parse").start();
                                                }
                                            }
                                            return null;
                                        }
                                    });
                        }
                    } catch (Throwable t2) {
                        cb = null;
                    }
                    m.invoke(x5, js, cb);
                    return;
                }
            }
            android.util.Log.i("PkHelper", "evaluateJavascript not found on " + x5.getClass().getName());
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "evalJs err " + t);
        }
    }

    private static void startLoops(final Object x5) {
        final int[] n = {0};
        final Runnable[] inject = new Runnable[1];
        inject[0] = new Runnable() {
            @Override
            public void run() {
                if (state == ST_IDLE) { return; }   // 外挂已关闭，停止注入
                evalJs(x5, HOOK_JS, false);
                if (n[0]++ < 10) {
                    main.postDelayed(inject[0], n[0] <= 5 ? 150 : 500);
                }
            }
        };
        main.post(inject[0]);
        final int[] p = {0};
        final Runnable[] poll = new Runnable[1];
        poll[0] = new Runnable() {
            @Override
            public void run() {
                if (state == ST_IDLE) { return; }   // 外挂已关闭，停止轮询
                evalJs(x5, "(function(){var d=window.__pkMatchData;if(d){window.__pkMatchData='';}return d===undefined?'':d;})()", true);
                if (p[0]++ < 40) {
                    main.postDelayed(poll[0], 900);
                }
            }
        };
        main.postDelayed(poll[0], 1200);
    }

    private static android.webkit.WebView findWebView(Activity activity) {
        try {
            android.view.ViewGroup root = activity.findViewById(android.R.id.content);
            if (root == null) {
                return null;
            }
            java.util.ArrayDeque<android.view.View> q = new java.util.ArrayDeque<>();
            q.add(root);
            while (!q.isEmpty()) {
                android.view.View v = q.poll();
                if (v instanceof android.webkit.WebView) {
                    return (android.webkit.WebView) v;
                }
                if (v instanceof android.view.ViewGroup) {
                    android.view.ViewGroup g = (android.view.ViewGroup) v;
                    for (int i = 0; i < g.getChildCount(); i++) {
                        q.add(g.getChildAt(i));
                    }
                }
            }
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "findWebView err " + t);
        }
        return null;
    }

    public static Response interceptResponse(Response response) {
        try {
            String url = response.request().url().toString();
            android.util.Log.i("PkHelper", "FLOW " + response.request().method() + " " + response.code() + " " + url);
            // 全量落盘：所有请求都记录（请求行 + 请求头 + 响应状态）
            capture("REQ " + response.request().method() + " " + url + " -> " + response.code());
            try {
                okhttp3.Headers h = response.request().headers();
                for (int i = 0; i < h.size(); i++) {
                    String v = h.value(i);
                    if (v != null && v.length() > 400) v = v.substring(0, 400) + "...";
                    capture("REQH " + h.name(i) + ": " + v);
                }
            } catch (Throwable ignore) {
            }
            try {
                okhttp3.Headers rh = response.headers();
                for (int i = 0; i < rh.size(); i++) {
                    String v = rh.value(i);
                    if (v != null && v.length() > 400) v = v.substring(0, 400) + "...";
                    capture("RESPH " + rh.name(i) + ": " + v);
                }
            } catch (Throwable ignore) {
            }
            try {
                String ck = response.request().header("Cookie");
                if (ck != null && ck.length() > 0) {
                    for (int i = 0; i < ck.length(); i += 700) {
                        android.util.Log.i("PkHelper", "CK[" + i + "]=" + ck.substring(i, Math.min(ck.length(), i + 700)));
                    }
                }
            } catch (Throwable ignore) {
            }
            if (url != null && (url.contains("auth") || url.contains("login") || url.contains("gateway") || url.contains("user-devices"))) {
                dumpRequest(response.request());
                android.util.Log.i("PkHelper", "RESP " + response.code() + " " + url);
                dumpResponseHeaders(response);
                dumpDeviceInfo();
            }
            if (url != null && url.contains(MATCH_KEY)) {
                lastMatchUrl = url;
                android.util.Log.i("PkHelper", "MATCH hit " + url);
                capture("MATCH hit " + url);
                dumpRequest(response.request());
                ResponseBody body = response.body();
                if (body != null) {
                    byte[] bytes = body.bytes();
                    android.util.Log.i("PkHelper", "MATCH bodyLen=" + bytes.length
                            + " head=" + new String(bytes, 0, Math.min(32, bytes.length), "UTF-8"));
                    capture("MATCH bodyLen=" + bytes.length + " b64="
                            + android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP));
                    JSONObject examVO = engine.handleEncryptedResponse(bytes);
                    android.util.Log.i("PkHelper", "MATCH examVO=" + (examVO == null ? "NULL" : "ok"));
                    return response.newBuilder().body(ResponseBody.create(body.contentType(), bytes)).build();
                } else {
                    android.util.Log.i("PkHelper", "MATCH body=null");
                }
            }
            if (response.code() >= 400) {
                ResponseBody body = response.body();
                if (body != null) {
                    byte[] bytes = body.bytes();
                    android.util.Log.i("PkHelper", "ERROR " + response.code() + " " + url + " BODY=" + new String(bytes, "UTF-8"));
                    capture("RESP " + response.code() + " " + url + " BODY=" + new String(bytes, "UTF-8"));
                    return response.newBuilder().body(ResponseBody.create(body.contentType(), bytes)).build();
                }
            }
        } catch (Throwable t) {
            lastError = "拦截异常: " + stack(t);
        }
        return response;
    }

    private static String errCode = "";

    private static void setErr(Activity a, String code, String detail) {
        errCode = code;
        lastError = code + " " + detail;
        if (button != null) {
            button.setCopyLabel(code == null || code.length() == 0 ? "复制报错" : code);
        }
        toast(a, lastError);
    }

    private static final int ST_IDLE = 0;
    private static final int ST_ARMED = 1;
    private static final int ST_DONE = 2;
    private static volatile int state = ST_IDLE;
    private static volatile boolean autoSubmitted;
    private static volatile boolean submitting;
    private static volatile String lastSubmittedPkId;
    private static volatile Object currentWebView;

    private static void setStatus(Activity a, String mainText, String copyCode) {
        // 遍历全部按钮：静态 button 可能指向别的页面，只更新它会让用户觉得"点了没反应"
        for (int i = buttons.size() - 1; i >= 0; i--) {
            PkFloatButton b = buttons.get(i);
            try {
                b.setAnswerLabel(mainText);
                if (copyCode != null) {
                    b.setCopyLabel(copyCode);
                }
            } catch (Throwable t) {
                buttons.remove(i);
            }
        }
        android.util.Log.i("PkHelper", "state=" + state + " ui=" + mainText);
    }

    /** 匹配失败横条：所有已注册按钮同步显示/隐藏 */
    private static void showRetryBar(final boolean show, final String text) {
        for (int i = buttons.size() - 1; i >= 0; i--) {
            PkFloatButton b = buttons.get(i);
            try {
                b.showRetryBar(show, text);
            } catch (Throwable t) {
                buttons.remove(i);
            }
        }
    }

    private static Runnable retryLoop;

    /** 每 3s 触发一次 H5 侧匹配重试，直到成功或用户点"取消"（间隔见循环内注释） */
    private static void startRetryLoop() {
        stopRetryLoop();
        retryLoop = new Runnable() {
            @Override
            public void run() {
                if (state != ST_ARMED) {
                    retryLoop = null;
                    return;
                }
                // 计数跟着"重试动作"走（每 3s +1），这样即便没收到失败响应，用户也能看到数字在跳
                retryCount++;
                showRetryBar(true, "匹配失败，重试中(" + retryCount + ")…");
                // 匹配失败页往往是新 document（原 hook 随旧页销毁 → __pkRetryMatch 找不到 → no-fn 空转），
                // 这里先幂等重注入 HOOK_JS（有 __pkHook 守卫），保证重试函数存在。
                evalJs(currentWebView, HOOK_JS, false);
                evalJs(currentWebView,
                        "(function(){try{ var r = (typeof window.__pkRetryMatch==='function') ? window.__pkRetryMatch()"
                                + " : 'no-fn'; try{ if(window.PkHook){PkHook.pkLog('RETRY '+r);} }catch(e2){} return r;}"
                                + "catch(e){return 'err:'+e}})()", false);
                // 服务端限流判定就是"请求过于频繁"，重试过快会持续坐实该判定并重置冷却。
                // 实测账号冷却约 60s，间隔可在设置里调（默认 3s）：既能自动接上，又不会自我加剧限流。
                int iv = appContext != null ? PkSettings.getRetryInterval(appContext) : 3;
                main.postDelayed(this, iv * 1000);
            }
        };
        main.postDelayed(retryLoop, 500);
    }

    private static void stopRetryLoop() {
        if (retryLoop != null) {
            main.removeCallbacks(retryLoop);
            retryLoop = null;
        }
    }

    private static void handleMainClick(final Activity activity) {
        main.post(new Runnable() {
            @Override
            public void run() {
                try {
                    android.util.Log.i("PkHelper", "CLICK state=" + state
                            + " buttons=" + buttons.size()
                            + " hasExam=" + (engine.getLastExamVO() != null)
                            + " submitted=" + autoSubmitted + " submitting=" + submitting
                            + " act=" + (activity == null ? "null" : activity.getClass().getSimpleName()));
                    // 开关语义：已就绪/自动中再点一次 = 真正关闭外挂
                    if (state == ST_ARMED) {
                        disableAuto();
                        setStatus(activity, "1秒答题", "");
                        toast(activity, "已关闭：外挂已停止，再点可重新开启");
                        return;
                    }
                    if (state == ST_DONE) {
                        state = ST_IDLE;
                        autoSubmitted = false;
                        setStatus(activity, "1秒答题", "");
                        toast(activity, "已重置：可重新开启");
                        return;
                    }
                    if (engine.getLastExamVO() != null) {
                        // 题目已抓到（用户在对局页才点按钮的情况）：开启并立即走完整直接交卷流程。
                        // 此前这里只调 submitNow 提交、不跳结果页，导致"提交成功但界面没反应"。
                        state = ST_ARMED;
                        autoSubmitted = false;
                        setStatus(activity, "自动中·点此关闭", "");
                        onCaptured(activity);
                        return;
                    }
                    state = ST_ARMED;
                    autoSubmitted = false;
                    setStatus(activity, "已就绪·点此关闭", "");
                    toast(activity, "已开启：现在进入对局，1 秒内自动完成");
                } catch (Throwable t) {
                    setErr(activity, "E08", "点击处理异常: " + t);
                }
            }
        });
    }

    /**
     * 关闭外挂：停掉 JS 侧自动答题循环并回到未开启状态。
     * 不清除 engine.onExamCaptured —— 它只在 attach 时设置，清掉后重新开启将无法再次触发；
     * 关闭后 onCaptured 开头会因 state != ST_ARMED 直接返回，因此是安全的。
     */
    private static void disableAuto() {
        try {
            Object x5 = currentWebView;
            if (x5 != null) {
                evalJs(x5, "(function(){try{"
                        + "if(window.__pkTimer){clearInterval(window.__pkTimer);window.__pkTimer=null;}"
                        + "window.__pkBusy=1;"
                        + "return 'ok';}catch(e){return 'err:'+e}})()", false);
            }
            android.util.Log.i("PkHelper", "auto disabled by user");
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "disableAuto err " + t);
        }
        state = ST_IDLE;
        autoSubmitted = false;
        submitting = false;
    }

    private static void onCaptured(final Activity activity) {
        if (state != ST_ARMED || autoSubmitted || submitting) {
            return;
        }
        main.post(new Runnable() {
            @Override
            public void run() {
                // 逐题快速答题：题目逐道显示并自动判对，由官方 H5 自行推进到 finishExercise 并跳结果页。
                // 保留作答过程观感（题目快速闪过），约 100ms/题，20 题约 2 秒
                startFastWrite(activity);
            }
        });
    }

    /**
     * 主路径：劫持识别桥 + 驱动逐题手写自动答题。
     * 题目逐道显示并自动判对，由官方 H5 自行推进到 finishExercise 并跳结果页。
     */
    private static void startFastWrite(final Activity activity) {
        try {
            lastRecvCount = 0;
            setStatus(activity, "自动中·点此关闭", "");
            // 注入设置项：单局时间 → 每题回调延迟（delay = 目标耗时/题数 - H5 固定开销约50ms）；
            // 人类化笔记开关/强度 → JS 侧 buildStrokes 抖动与步进节奏
            int qn = engine.getQuestionCount() > 0 ? engine.getQuestionCount() : 30;
            int perQ = PkSettings.getRoundTime(activity) * 1000 / qn;
            int pkDelay = Math.max(10, perQ - 50);
            int pkJit = Math.max(5, Math.min(300, pkDelay / 2));
            evalJs(currentWebView,
                    "window.__pkDelay=" + pkDelay + ";window.__pkJit=" + pkJit
                            + ";window.__pkHuman=" + (PkSettings.getHumanStroke(activity) ? 1 : 0)
                            + ";window.__pkInt=" + PkSettings.getIntensity(activity) + ";", false);
            android.util.Log.i("PkHelper", "settings delay=" + pkDelay + " jit=" + pkJit
                    + " roundTime=" + PkSettings.getRoundTime(activity) + "s q=" + qn);
            evalJs(currentWebView, AUTO_ANSWER_JS, false);
            android.util.Log.i("PkHelper", "AUTO_ANSWER_JS injected");
            if (currentWebView != null) {
                int q = engine.getQuestionCount();
                int times = q > 0 ? (q + 8) : 32;
                evalJs(currentWebView, "window.__pkAutoStart(30," + times + ")", false);
                android.util.Log.i("PkHelper", "auto start times=" + times + " q=" + q);
                    main.postDelayed(new Runnable() {
                        private int k;

                        @Override
                        public void run() {
                            evalJs(currentWebView, "try{PkHook.pkLog('P d='+(window.__pkDraw|0)+' r='+(window.__pkRecv|0)"
                                    + "+' s='+(window.__pkSwallow|0)+' c='+document.querySelectorAll('canvas').length+' u='+location.href)}catch(e){}", false);
                            // 仅轮询上报进度；不再自动关闭（按要求：被限流时用户可自行关闭）
                            if (k++ < 20) {
                                main.postDelayed(this, 500);
                            }
                        }
                    }, 800);
                }
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "startFastWrite err " + t);
        }
    }

    private static void submitNow(final Activity activity) {
        if (submitting || autoSubmitted) {
            return;
        }
        String pk = engine.getPkIdStr();
        if (pk != null && pk.equals(lastSubmittedPkId)) {
            android.util.Log.i("PkHelper", "submitNow skip: already submitted pk=" + pk);
            return;
        }
        submitting = true;
        try {
            final JSONObject card = engine.buildAnswerCard();
            if (card == null) {
                submitting = false;
                if (engine.getLastExamVO() == null) {
                    setErr(activity, "E01", "未捕获到题目数据：match 响应未抓到（若刚进对局，请再开一局重试）");
                } else {
                    setErr(activity, "E04", "题目数据异常：examVO 缺 questions");
                }
                if (state == ST_ARMED) {
                    setStatus(activity, "就绪等待中", errCode);
                }
                return;
            }
            new Thread(new Runnable() {
                @Override
                public void run() {
                    final boolean ok = submit(card);
                    main.post(new Runnable() {
                        @Override
                        public void run() {
                            submitting = false;
                            if (ok) {
                                autoSubmitted = true;
                                lastSubmittedPkId = engine.getPkIdStr();
                                state = ST_DONE;
                                lastError = "";
                                errCode = "";
                                if (button != null) {
                                    button.setAnswerLabel("已完成·秒答成功");
                                    button.setCopyLabel("复制报错");
                                }
                                toast(activity, "已提交，1秒完成全部题目");
                            } else {
                                toast(activity, lastError);
                                if (state == ST_ARMED) {
                                    setStatus(activity, "提交失败·再点重试", errCode);
                                }
                            }
                        }
                    });
                }
            }, "pk-submit").start();
        } catch (Throwable t) {
            submitting = false;
            setErr(activity, "E08", "答题异常: " + t);
        }
    }

    private static boolean submit(JSONObject card) {
        try {
            byte[] body = engine.encryptToBytes(card);
            if (body == null || body.length == 0) {
                lastError = "加密答题卡失败";
                return false;
            }
            String host = hostOf(lastMatchUrl);
            if (host == null) host = "https://xyks.yuanfudao.com";
            String url = host + SUBMIT_PATH;

            Request request = new Request.Builder()
                    .url(url)
                    .put(RequestBody.create(MediaType.parse("application/octet-stream"), body))
                    .build();
            OkHttpClient client = qp.i.a.s();
            Response resp = client.newCall(request).execute();
            int code = resp.code();
            String respInfo = "";
            try {
                ResponseBody rb = resp.body();
                if (rb != null) {
                    byte[] rbBytes = rb.bytes();
                    respInfo = new String(rbBytes, 0, Math.min(1500, rbBytes.length), "UTF-8");
                }
            } catch (Throwable t2) {
                respInfo = "respReadErr " + t2;
            }
            android.util.Log.i("PkHelper", "SUBMIT code=" + code + " resp=" + respInfo);
            resp.close();
            if (code >= 200 && code < 300) {
                try {
                    Thread.sleep(3000);   // 等服务器落库后再查判分
                } catch (Throwable ignore) {
                }
                fetchResultDetail();
                storeResultForH5();
                return true;
            }
            lastError = "HTTP " + code;
            return false;
        } catch (Throwable t) {
            lastError = "提交异常: " + stack(t);
            return false;
        }
    }

    /**
     * 提交后用官方结果页同款接口查询服务器真实判分（完全确定的验证手段）。
     */
    private static void fetchResultDetail() {
        try {
            String pkIdStr = engine.getPkIdStr();
            if (pkIdStr == null || pkIdStr.length() == 0) {
                android.util.Log.i("PkHelper", "RESULT pkIdStr empty");
                return;
            }
            String host = hostOf(lastMatchUrl);
            if (host == null) host = "https://xyks.yuanfudao.com";
            String url = host + "/leo-game-pk/android/math/pk/history/detail?pkIdStr=" + pkIdStr;
            Request req = new Request.Builder().url(url).get().build();
            OkHttpClient client = qp.i.a.s();
            Response r = client.newCall(req).execute();
            int c = r.code();
            String body = "";
            try {
                ResponseBody rb = r.body();
                if (rb != null) {
                    byte[] b = rb.bytes();
                    body = new String(b, 0, Math.min(2000, b.length), "UTF-8");
                }
            } catch (Throwable t) {
                body = "readErr " + t;
            }
            android.util.Log.i("PkHelper", "RESULT code=" + c + " pkIdStr=" + pkIdStr);
            for (int i = 0; i < body.length(); i += 900) {
                android.util.Log.i("PkHelper", "RESULT_BODY[" + i + "]=" + body.substring(i, Math.min(body.length(), i + 900)));
            }
            r.close();
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "RESULT err " + t);
        }
    }

    /**
     * 官方结果页读的是 H5 本地存储（exerciseResult + STORAGE_KEY_LAST_PK_ID），
     * 而非直接查服务器。我们绕过答题页提交，需自行写入本地结果，否则结果页显示异常。
     */
    private static void storeResultForH5() {
        try {
            String pk = engine.getPkIdStr();
            JSONObject card = engine.buildAnswerCard();
            if (pk == null || card == null) {
                android.util.Log.i("PkHelper", "storeResult skip pk/card null");
                return;
            }
            // 存储层约定（StorageUtil-legacy）：key = "__local_" + name，值 = Base64.encode(json)
            // 结果页用 getItemWithException("exerciseResult") 读取，必须严格匹配此约定；
            // 旧版直接写 localStorage['exerciseResult']=明文 → 结果页读到空 → 显示"一道题没答"
            final String b64 = Base64.encodeToString(card.toString().getBytes("UTF-8"), Base64.NO_WRAP);
            final String pkF = pk;
            main.post(new Runnable() {
                @Override
                public void run() {
                    Object x5 = currentWebView;
                    if (x5 == null) {
                        android.util.Log.i("PkHelper", "storeResult no webview");
                        return;
                    }
                    String js = "(function(){try{"
                            + "localStorage.setItem('__local_exerciseResult','" + b64 + "');"
                            + "return 'ok';}catch(e){return 'err:'+e}})()";
                    evalJs(x5, js, false);
                    android.util.Log.i("PkHelper", "storeResult injected pk=" + pkF + " b64len=" + b64.length());
                }
            });
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "storeResult err " + t);
        }
    }

    /**
     * 从 match URL 推断结果页的 subject 参数。
     * 数学/语文结果页不带 subject；英语单词与单词消除共用 result.html，靠 subject 区分。
     */
    private static String subjectOfMatch(String url) {
        if (url == null) {
            return "";
        }
        if (url.contains("/word/eliminate/")) {
            return "englishEli";
        }
        if (url.contains("/english/")) {
            return "english";
        }
        return "";
    }

    /**
     * 直接跳转结果页。结果页会自己读 localStorage(__local_exerciseResult) 并调用
     * postPkExerciseResult 提交服务器 —— 走官方链路，且与题型（手写/点击/连线）无关。
     * 结果页路径从当前页面 location 推导 bundle 名，自动适配 oral-pk / poem-pk。
     */
    private static void gotoResultPage() {
        try {
            final String pk = engine.getPkIdStr();
            if (pk == null) {
                android.util.Log.i("PkHelper", "gotoResult skip pk null");
                return;
            }
            final String subj = subjectOfMatch(lastMatchUrl);
            main.post(new Runnable() {
                @Override
                public void run() {
                    Object x5 = currentWebView;
                    if (x5 == null) {
                        android.util.Log.i("PkHelper", "gotoResult no webview");
                        return;
                    }
                    String js = "(function(){try{"
                            + "var pk='" + pk + "';var subj='" + subj + "';"
                            + "var p=location.pathname||'';var m=p.match(/^\\/bh5\\/([^\\/]+)\\//);"
                            + "var b=m?m[1]:'leo-web-oral-pk';"
                            + "var u=location.origin+'/bh5/'+b+'/result.html?pkIdStr='+encodeURIComponent(pk);"
                            + "if(subj){u+='&subject='+subj;}"
                            // 与官方 gotoPkResultPage 一致：通过 native://openWebView 开新 WebView 承载结果页
                            + "var n='native://openWebView?url='+encodeURIComponent(u)"
                            + "+'&hideNavigation=true&immerseStatusBar=true&autoHideLoading=false&isFullScreen=true';"
                            + "window.location.href=n;return 'ok';"
                            + "}catch(e){return 'err:'+e}})()";
                    evalJs(x5, js, false);
                    android.util.Log.i("PkHelper", "gotoResult injected pk=" + pk + " subj=" + subj);
                }
            });
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "gotoResult err " + t);
        }
    }

    public static String getLastError() {
        return lastError;
    }

    private static void dumpRequest(Request req) {
        try {
            android.util.Log.i("PkHelper", "REQ " + req.method() + " " + req.url());
            capture("REQ " + req.method() + " " + req.url());
            okhttp3.Headers hs = req.headers();
            for (int i = 0; i < hs.size(); i++) {
                String v = hs.value(i);
                if (v != null && v.length() > 180) v = v.substring(0, 180) + "...";
                android.util.Log.i("PkHelper", "REQH " + hs.name(i) + "=" + v);
                capture("REQH " + hs.name(i) + ": " + v);
            }
            RequestBody rb = req.body();
            if (rb != null) {
                try {
                    okio.Buffer buf = new okio.Buffer();
                    rb.writeTo(buf);
                    long size = buf.size();
                    byte[] data = size > 600 ? new byte[600] : new byte[(int) size];
                    buf.readFully(data);
                    String b64 = android.util.Base64.encodeToString(data, android.util.Base64.NO_WRAP);
                    android.util.Log.i("PkHelper", "REQBODY len=" + size + " b64=" + b64);
                    capture("REQBODY len=" + size + " b64=" + b64);
                } catch (Throwable t5) {
                    android.util.Log.i("PkHelper", "REQBODY err " + t5);
                }
            }
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "dumpReq err " + t);
        }
    }

    private static void dumpResponseHeaders(Response response) {
        try {
            okhttp3.Headers hs = response.headers();
            for (int i = 0; i < hs.size(); i++) {
                String v = hs.value(i);
                if (v != null && v.length() > 180) v = v.substring(0, 180) + "...";
                android.util.Log.i("PkHelper", "RESPH " + hs.name(i) + "=" + v);
            }
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "dumpResp err " + t);
        }
    }

    private static void dumpDeviceInfo() {
        try {
            android.util.Log.i("PkHelper", "CPU_ABI=" + android.os.Build.CPU_ABI + " CPU_ABI2=" + android.os.Build.CPU_ABI2);
            android.util.Log.i("PkHelper", "HW=" + android.os.Build.HARDWARE + " BOARD=" + android.os.Build.BOARD + " DEVICE=" + android.os.Build.DEVICE + " PRODUCT=" + android.os.Build.PRODUCT);
            android.util.Log.i("PkHelper", "BRAND=" + android.os.Build.BRAND + " MODEL=" + android.os.Build.MODEL + " MFG=" + android.os.Build.MANUFACTURER);
            try {
                android.app.Application app = (android.app.Application) Class.forName("android.app.ActivityThread").getMethod("currentApplication").invoke(null);
                String sysAid = android.provider.Settings.Secure.getString(app.getContentResolver(), "android_id");
                android.util.Log.i("PkHelper", "Settings.Secure android_id=" + sysAid);
            } catch (Throwable t3) {
                android.util.Log.i("PkHelper", "sys aid err " + t3);
            }
            try {
                Class<?> i3c = Class.forName("nr.i3");
                Object i3 = i3c.getMethod("c").invoke(null);
                String uuid = (String) i3c.getMethod("d").invoke(i3);
                String aid = (String) i3c.getMethod("a").invoke(i3);
                android.util.Log.i("PkHelper", "UUID=" + uuid + " android_id(i3.a)=" + aid);
            } catch (Throwable t2) {
                android.util.Log.i("PkHelper", "i3 err " + t2);
            }
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "dump err " + t);
        }
    }

    public static void copyError(Activity activity) {
        try {
            ClipboardManager cm = (ClipboardManager) activity.getSystemService(Context.CLIPBOARD_SERVICE);
            cm.setText("小猿口算1秒答题报错：\n" + lastError);
            toast(activity, "报错已复制到剪贴板");
        } catch (Throwable t) {
            toast(activity, "复制失败");
        }
    }

    private static String hostOf(String url) {
        if (url == null) return null;
        try {
            java.net.URL u = new java.net.URL(url);
            return u.getProtocol() + "://" + u.getHost();
        } catch (Throwable t) {
            return null;
        }
    }

    private static String stack(Throwable t) {
        StringWriter sw = new StringWriter();
        t.printStackTrace(new PrintWriter(sw));
        return t.getClass().getName() + ": " + t.getMessage() + "\n" + sw.toString();
    }

    private static Toast lastToast;

    private static void toast(Activity a, String msg) {
        try {
            android.util.Log.i("PkHelper", "TOAST " + msg);
            // 设置项「界面提示」关闭时不弹 Toast（logcat 与落盘日志不受影响）
            Context gateC = (a != null && !a.isFinishing()) ? a.getApplicationContext() : appContext;
            if (gateC != null && !PkSettings.getToastEnabled(gateC)) {
                return;
            }
            // 页面可能已 finish（如匹配失败后返回），此时用 Application context 兜底，
            // 否则 Toast 静默失败，用户会以为"点了没反应"
            Context c = null;
            if (a != null && !a.isFinishing()) {
                c = a.getApplicationContext();
            }
            if (c == null) {
                c = appContext;
            }
            if (c == null) {
                return;
            }
            if (lastToast == null) {
                lastToast = Toast.makeText(c, msg, Toast.LENGTH_SHORT);
            } else {
                lastToast.setText(msg);
                lastToast.setDuration(Toast.LENGTH_SHORT);
            }
            lastToast.show();
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "toast err " + t);
        }
    }
}
