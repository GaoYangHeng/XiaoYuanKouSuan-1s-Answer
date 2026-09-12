// 片段：DEX 注入入口与页面守卫
// 说明：在目标 WebActivity.onCreate 中插桩调用 attach()，由它决定是否挂载悬浮控件与注入脚本。
// 已脱敏，仅保留逻辑骨架。

public class PkHelper {

    // 只在数学 PK 的两个页面生效；语文/英语为独立页面，显式排除
    private static final String PK_PAGE_KEY = "leo-web-oral-pk/";

    private static boolean isMathPkPage(String url) {
        if (url == null || !url.contains(PK_PAGE_KEY)) {
            return false;
        }
        // 英语页面位于同一个包内，需单独排除
        if (url.contains("english-words.html") || url.contains("english-word-match.html")) {
            return false;
        }
        return url.contains("exercise.html") || url.contains("pk.html");
    }

    public static void attach(final Activity activity) {
        final String url = extractUrl(activity);   // 从 Intent 的 url / pagePath / data 中取
        if (!isMathPkPage(url)) {
            return;
        }

        // 1. 挂载悬浮按钮（可开关；文案反映当前状态）
        PkFloatButton button = new PkFloatButton(activity, new Runnable() {
            @Override public void run() { handleMainClick(activity); }
        });
        buttons.add(button);
        main.post(new Runnable() {
            @Override public void run() { button.show(); }
        });

        // 2. 进入对局页：重置上一局残留状态，避免跨局串味
        if (url.contains("exercise.html")) {
            autoSubmitted = false;
            submitting = false;
            lastSubmittedPkId = null;
        }

        // 3. 取 WebView 并注入 JS Bridge
        installHook(activity);
    }

    // 取 WebView：优先走官方同款路径，失败再退回 View 树扫描
    private static Object getX5WebView(Activity activity) {
        try {
            Object webApp = activity.getClass().getMethod("getWebApp").invoke(activity);
            if (webApp != null) {
                Object wv = webApp.getClass().getMethod("getWebView").invoke(webApp);
                if (wv != null) { return wv; }
            }
        } catch (Throwable t) { /* 忽略 */ }
        return findWebView(activity);   // BFS 扫描 android.R.id.content
    }

    // 通过反射调用 evaluateJavascript（Callback 用动态代理接住返回值）
    private static void evalJs(Object webView, String js, boolean readResult) { /* ... */ }

    private static void handleMainClick(Activity activity) {
        // 开关语义：未开→开启；已开→关闭并复位文案
        if (state == ST_ARMED) {
            disableAuto();
            setStatus(activity, "1秒答题", "");
            toast(activity, "已关闭");
        } else {
            state = ST_ARMED;
            setStatus(activity, "已就绪·点此关闭", "");
            toast(activity, "已开启");
        }
    }
}
