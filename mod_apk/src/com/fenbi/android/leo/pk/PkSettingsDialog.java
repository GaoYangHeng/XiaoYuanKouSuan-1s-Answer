package com.fenbi.android.leo.pk;

import android.app.Activity;
import android.app.Dialog;
import android.graphics.Color;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.Switch;
import android.widget.TextView;

/**
 * 外挂设置小窗口（纯代码构建，无需 res 资源）。
 * 退出方式三选一：右上角 ✕ / 系统返回键 / 点击窗口外空白区域。
 * 所有设置项即时保存（SharedPreferences），无需确定按钮。
 */
public class PkSettingsDialog {

    public static void show(final Activity activity) {
        final Dialog dlg = new Dialog(activity);
        dlg.requestWindowFeature(Window.FEATURE_NO_TITLE);

        final LinearLayout root = new LinearLayout(activity);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF263238);
        root.setPadding(dp(activity, 16), dp(activity, 12), dp(activity, 16), dp(activity, 16));

        // ---------- 标题行：标题 + 右上角关闭叉 ----------
        LinearLayout header = new LinearLayout(activity);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);

        TextView title = new TextView(activity);
        title.setText("1秒答题 · 设置");
        title.setTextColor(Color.WHITE);
        title.setTextSize(15);
        LinearLayout.LayoutParams lpTitle = new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
        header.addView(title, lpTitle);

        TextView close = new TextView(activity);
        close.setText("✕");
        close.setTextColor(0xFFFF8A65);
        close.setTextSize(20);
        close.setGravity(Gravity.CENTER);
        close.setPadding(dp(activity, 10), dp(activity, 2), dp(activity, 10), dp(activity, 2));
        close.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                dlg.dismiss();
            }
        });
        header.addView(close);
        root.addView(header);

        root.addView(sep(activity));

        // ---------- 1. 单局时间（秒，1-4；更大值受回调封顶限制无效）----------
        final TextView roundVal = new TextView(activity);
        SeekBar round = seek(activity, 1, 4, PkSettings.getRoundTime(activity) - 1);
        row(root, "单局时间", "自动答完一局的目标耗时（1-4 秒）", roundVal, "秒");
        roundVal.setText(String.valueOf(PkSettings.getRoundTime(activity)));
        round.setOnSeekBarChangeListener(new SimpleSeek() {
            @Override
            public void onProgressChanged(SeekBar sb, int progress, boolean fromUser) {
                int v = progress + 1;
                PkSettings.setRoundTime(activity, v);
                roundVal.setText(String.valueOf(v));
            }
        });
        root.addView(round);

        // ---------- 2. 人类化笔记开关 ----------
        final Switch human = new Switch(activity);
        human.setChecked(PkSettings.getHumanStroke(activity));
        human.setTextColor(0xFFECEFF1);
        human.setTextSize(13);
        switchRow(root, "人类化笔记", "关闭 = 机械笔迹（无抖动、最快步进）", human);
        human.setOnCheckedChangeListener(new android.widget.CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(android.widget.CompoundButton btn, boolean checked) {
                PkSettings.setHumanStroke(activity, checked);
            }
        });

        // ---------- 3. 笔记强度 ----------
        final TextView intVal = new TextView(activity);
        SeekBar intensity = seek(activity, 0, 100, PkSettings.getIntensity(activity));
        row(root, "笔记强度", "笔迹坐标抖动幅度（人类化笔记开启时生效）", intVal, "%");
        intVal.setText(PkSettings.getIntensity(activity) + "%");
        intensity.setOnSeekBarChangeListener(new SimpleSeek() {
            @Override
            public void onProgressChanged(SeekBar sb, int progress, boolean fromUser) {
                PkSettings.setIntensity(activity, progress);
                intVal.setText(progress + "%");
            }
        });
        root.addView(intensity);

        // ---------- 4. 匹配失败重试间隔（秒）----------
        final TextView retryVal = new TextView(activity);
        SeekBar retry = seek(activity, 3, 30, PkSettings.getRetryInterval(activity) - 3);
        row(root, "重试间隔", "匹配失败后自动重试的间隔（防触发限流勿调太小）", retryVal, "秒");
        retryVal.setText(String.valueOf(PkSettings.getRetryInterval(activity)));
        retry.setOnSeekBarChangeListener(new SimpleSeek() {
            @Override
            public void onProgressChanged(SeekBar sb, int progress, boolean fromUser) {
                int v = progress + 3;
                PkSettings.setRetryInterval(activity, v);
                retryVal.setText(String.valueOf(v));
            }
        });
        root.addView(retry);

        // ---------- 5. 进入对局页自动开启 ----------
        final Switch autoArm = new Switch(activity);
        autoArm.setChecked(PkSettings.getAutoArm(activity));
        autoArm.setTextColor(0xFFECEFF1);
        autoArm.setTextSize(13);
        switchRow(root, "自动开启", "进入 PK 页自动武装，无需手动点按钮", autoArm);
        autoArm.setOnCheckedChangeListener(new android.widget.CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(android.widget.CompoundButton btn, boolean checked) {
                PkSettings.setAutoArm(activity, checked);
            }
        });

        // ---------- 6. Toast 提示开关 ----------
        final Switch toastSw = new Switch(activity);
        toastSw.setChecked(PkSettings.getToastEnabled(activity));
        toastSw.setTextColor(0xFFECEFF1);
        toastSw.setTextSize(13);
        switchRow(root, "界面提示", "关闭后不再弹 Toast（日志不受影响）", toastSw);
        toastSw.setOnCheckedChangeListener(new android.widget.CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(android.widget.CompoundButton btn, boolean checked) {
                PkSettings.setToastEnabled(activity, checked);
            }
        });

        dlg.setContentView(root);
        // 三种退出方式：返回键（cancelable 默认 true）+ 点击外部空白 + 右上角叉
        dlg.setCancelable(true);
        dlg.setCanceledOnTouchOutside(true);

        Window w = dlg.getWindow();
        if (w != null) {
            w.setBackgroundDrawableResource(android.R.color.transparent);
        }
        dlg.show();
        if (w != null) {
            int screenW = activity.getResources().getDisplayMetrics().widthPixels;
            int width = Math.min(screenW - dp(activity, 48), dp(activity, 340));
            w.setLayout(width, ViewGroup.LayoutParams.WRAP_CONTENT);
            w.setGravity(Gravity.CENTER);
        }
    }

    // ---------- 布局小工具 ----------

    private static void row(LinearLayout root, String label, String hint,
                            TextView valueView, String unit) {
        LinearLayout line = new LinearLayout(root.getContext());
        line.setOrientation(LinearLayout.HORIZONTAL);
        line.setGravity(Gravity.CENTER_VERTICAL);

        TextView tv = new TextView(root.getContext());
        tv.setText(label);
        tv.setTextColor(0xFFFFFFFF);
        tv.setTextSize(14);
        LinearLayout.LayoutParams lpL = new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
        line.addView(tv, lpL);

        valueView.setTextColor(0xFFFFAB91);
        valueView.setTextSize(15);
        line.addView(valueView);
        TextView u = new TextView(root.getContext());
        u.setText(" " + unit);
        u.setTextColor(0xFF90A4AE);
        u.setTextSize(12);
        line.addView(u);

        root.addView(line);
        TextView h = new TextView(root.getContext());
        h.setText(hint);
        h.setTextColor(0xFF78909C);
        h.setTextSize(11);
        root.addView(h);
    }

    private static void switchRow(LinearLayout root, String label, String hint, Switch sw) {
        LinearLayout line = new LinearLayout(root.getContext());
        line.setOrientation(LinearLayout.HORIZONTAL);
        line.setGravity(Gravity.CENTER_VERTICAL);
        line.setPadding(0, dp(root.getContext(), 6), 0, dp(root.getContext(), 6));

        LinearLayout texts = new LinearLayout(root.getContext());
        texts.setOrientation(LinearLayout.VERTICAL);
        TextView tv = new TextView(root.getContext());
        tv.setText(label);
        tv.setTextColor(0xFFFFFFFF);
        tv.setTextSize(14);
        texts.addView(tv);
        TextView h = new TextView(root.getContext());
        h.setText(hint);
        h.setTextColor(0xFF78909C);
        h.setTextSize(11);
        texts.addView(h);

        LinearLayout.LayoutParams lpT = new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
        line.addView(texts, lpT);
        line.addView(sw);
        root.addView(line);
    }

    private static SeekBar seek(android.content.Context c, int min, int max, int progress) {
        SeekBar sb = new SeekBar(c);
        sb.setMax(max - min);
        sb.setProgress(Math.max(0, Math.min(max - min, progress)));
        sb.setPadding(0, dp(c, 6), 0, dp(c, 10));
        return sb;
    }

    private static View sep(android.content.Context c) {
        View v = new View(c);
        v.setBackgroundColor(0x33FFFFFF);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(c, 1));
        lp.topMargin = dp(c, 10);
        lp.bottomMargin = dp(c, 6);
        v.setLayoutParams(lp);
        return v;
    }

    private static int dp(android.content.Context c, int v) {
        return (int) (v * c.getResources().getDisplayMetrics().density + 0.5f);
    }

    /** SeekBar 监听样板：只关心进度变化 */
    private abstract static class SimpleSeek implements SeekBar.OnSeekBarChangeListener {
        @Override
        public void onStartTrackingTouch(SeekBar sb) {
        }

        @Override
        public void onStopTrackingTouch(SeekBar sb) {
        }
    }
}
