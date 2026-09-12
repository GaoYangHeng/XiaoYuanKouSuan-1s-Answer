package com.fenbi.android.leo.pk;

import android.app.Activity;
import android.graphics.Color;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * 比大小 PK 页的可拖动悬浮按钮：主按钮「1秒答题」+ 副按钮「复制报错」。
 * 长按拖动改变位置，单击主按钮触发答题，单击副按钮复制最近一次报错信息。
 */
public class PkFloatButton {
    private final Activity activity;
    private final LinearLayout container;
    private final TextView answerBtn;
    private final TextView copyBtn;
    /** 匹配失败时显示的横条：文案 + 取消按钮 */
    private final LinearLayout retryBar;
    private final TextView retryText;
    private final TextView retryCancel;
    private Runnable onRetryCancel;
    private final Runnable onClick;
    private float downX, downY;
    private int startLeft, startTop;
    private boolean dragging;
    private static final int CLICK_SLOP = 12;

    public PkFloatButton(Activity activity, Runnable onClick) {
        this.activity = activity;
        this.onClick = onClick;

        this.container = new LinearLayout(activity);
        container.setOrientation(LinearLayout.VERTICAL);
        container.setGravity(Gravity.CENTER);
        container.setElevation(dp(6));

        this.answerBtn = makeButton("1秒答题", 0xCCFF5722, 14, dp(14), dp(10));
        this.copyBtn = makeButton("复制报错", 0xCC333333, 12, dp(10), dp(6));

        container.addView(answerBtn);
        container.addView(copyBtn);

        // 匹配失败横条（默认隐藏）
        this.retryBar = new LinearLayout(activity);
        retryBar.setOrientation(LinearLayout.HORIZONTAL);
        retryBar.setGravity(Gravity.CENTER_VERTICAL);
        retryBar.setBackgroundColor(0xDD37474F);
        retryBar.setPadding(dp(10), dp(7), dp(10), dp(7));
        retryBar.setVisibility(View.GONE);

        this.retryText = new TextView(activity);
        retryText.setText("匹配失败，正在重试…");
        retryText.setTextColor(Color.WHITE);
        retryText.setTextSize(12);
        this.retryCancel = makeButton("取消", 0xCCFF5722, 12, dp(10), dp(5));
        LinearLayout.LayoutParams lpCancel = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lpCancel.leftMargin = dp(10);
        retryCancel.setLayoutParams(lpCancel);

        retryBar.addView(retryText);
        retryBar.addView(retryCancel);
        container.addView(retryBar);

        container.setOnTouchListener(new View.OnTouchListener() {
            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        downX = event.getRawX();
                        downY = event.getRawY();
                        startLeft = v.getLeft();
                        startTop = v.getTop();
                        dragging = false;
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        float dx = event.getRawX() - downX;
                        float dy = event.getRawY() - downY;
                        if (!dragging && (Math.abs(dx) > CLICK_SLOP || Math.abs(dy) > CLICK_SLOP)) {
                            dragging = true;
                        }
                        if (dragging) {
                            int nl = startLeft + (int) dx;
                            int nt = startTop + (int) dy;
                            ViewGroup parent = (ViewGroup) v.getParent();
                            if (parent != null) {
                                nl = clamp(nl, 0, parent.getWidth() - v.getWidth());
                                nt = clamp(nt, 0, parent.getHeight() - v.getHeight());
                            }
                            v.layout(nl, nt, nl + v.getWidth(), nt + v.getHeight());
                        }
                        return true;
                    case MotionEvent.ACTION_UP:
                        if (!dragging) {
                            dispatchClick(event.getX(), event.getY());
                        }
                        return true;
                }
                return false;
            }
        });
    }

    private TextView makeButton(String text, int color, int textSize, int padX, int padY) {
        TextView tv = new TextView(activity);
        tv.setText(text);
        tv.setTextColor(Color.WHITE);
        tv.setTextSize(textSize);
        tv.setGravity(Gravity.CENTER);
        tv.setBackgroundColor(color);
        tv.setPadding(padX, padY, padX, padY);
        return tv;
    }

    private void dispatchClick(float x, float y) {
        if (y >= answerBtn.getTop() && y <= answerBtn.getBottom()) {
            if (onClick != null) onClick.run();
        } else if (y >= copyBtn.getTop() && y <= copyBtn.getBottom()) {
            PkHelper.copyError(activity);
        } else if (retryBar.getVisibility() == View.VISIBLE
                && y >= retryBar.getTop() && y <= retryBar.getBottom()) {
            // 横条内：只有右侧"取消"热区响应，其余区域不误触
            if (x >= retryCancel.getLeft() && x <= retryCancel.getRight()) {
                if (onRetryCancel != null) {
                    onRetryCancel.run();
                }
            }
        }
    }

    /** 显示/隐藏"匹配失败，正在重试"横条 */
    public void showRetryBar(boolean show, String text) {
        if (text != null) {
            retryText.setText(text);
        }
        retryBar.setVisibility(show ? View.VISIBLE : View.GONE);
    }

    /** 设置横条上"取消"的回调 */
    public void setOnRetryCancel(Runnable r) {
        this.onRetryCancel = r;
    }

    private static int clamp(int v, int min, int max) {
        if (max < min) return min;
        return Math.max(min, Math.min(max, v));
    }

    private int dp(int v) {
        return (int) (v * activity.getResources().getDisplayMetrics().density + 0.5f);
    }

    public void setCopyLabel(String text) {
        copyBtn.setText(text);
    }

    public void setAnswerLabel(String text) {
        answerBtn.setText(text);
    }

    public void show() {
        ViewGroup root = activity.findViewById(android.R.id.content);
        if (root == null || container.getParent() != null) return;
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.END | Gravity.BOTTOM);
        lp.rightMargin = dp(16);
        lp.bottomMargin = dp(180);
        root.addView(container, lp);
    }

    public void hide() {
        ViewGroup parent = (ViewGroup) container.getParent();
        if (parent != null) {
            parent.removeView(container);
        }
    }
}
