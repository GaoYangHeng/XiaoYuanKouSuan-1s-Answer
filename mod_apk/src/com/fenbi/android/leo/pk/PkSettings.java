package com.fenbi.android.leo.pk;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * 悬浮窗外挂设置项持久化（SharedPreferences: pk_settings）。
 * 所有读取均带默认值，写入时夹取到合法区间，供 PkHelper / PkSettingsDialog 共用。
 */
public class PkSettings {
    private static final String NAME = "pk_settings";

    public static final int DEF_ROUND_TIME = 2;          // 单局时间（秒）：自动答完一局的目标耗时
    // 上限 4 秒：回调延迟封顶 60ms（JS 侧 min），更大值不会更慢（避免 H5 识别超时卡题）
    public static final boolean DEF_HUMAN_STROKE = true; // 人类化笔记开关
    public static final int DEF_INTENSITY = 50;          // 笔记强度 0-100
    public static final int DEF_RETRY_INTERVAL = 3;      // 匹配失败重试间隔（秒）
    public static final boolean DEF_AUTO_ARM = false;    // 进入对局页自动开启
    public static final boolean DEF_TOAST = true;        // Toast 提示开关

    private static SharedPreferences sp(Context c) {
        return c.getSharedPreferences(NAME, Context.MODE_PRIVATE);
    }

    public static int getRoundTime(Context c) {
        // 读取侧也 clamp：兼容此前版本可能存下的超上限旧值
        return clamp(sp(c).getInt("round_time", DEF_ROUND_TIME), 1, 4);
    }

    public static void setRoundTime(Context c, int v) {
        sp(c).edit().putInt("round_time", clamp(v, 1, 4)).apply();
    }

    public static boolean getHumanStroke(Context c) {
        return sp(c).getBoolean("human_stroke", DEF_HUMAN_STROKE);
    }

    public static void setHumanStroke(Context c, boolean v) {
        sp(c).edit().putBoolean("human_stroke", v).apply();
    }

    public static int getIntensity(Context c) {
        return sp(c).getInt("intensity", DEF_INTENSITY);
    }

    public static void setIntensity(Context c, int v) {
        sp(c).edit().putInt("intensity", clamp(v, 0, 100)).apply();
    }

    public static int getRetryInterval(Context c) {
        return sp(c).getInt("retry_interval", DEF_RETRY_INTERVAL);
    }

    public static void setRetryInterval(Context c, int v) {
        sp(c).edit().putInt("retry_interval", clamp(v, 3, 30)).apply();
    }

    public static boolean getAutoArm(Context c) {
        return sp(c).getBoolean("auto_arm", DEF_AUTO_ARM);
    }

    public static void setAutoArm(Context c, boolean v) {
        sp(c).edit().putBoolean("auto_arm", v).apply();
    }

    public static boolean getToastEnabled(Context c) {
        return sp(c).getBoolean("toast", DEF_TOAST);
    }

    public static void setToastEnabled(Context c, boolean v) {
        sp(c).edit().putBoolean("toast", v).apply();
    }

    private static int clamp(int v, int lo, int hi) {
        return Math.max(lo, Math.min(hi, v));
    }
}
