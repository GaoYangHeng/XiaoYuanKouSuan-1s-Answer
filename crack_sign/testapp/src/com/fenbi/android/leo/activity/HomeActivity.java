package com.fenbi.android.leo.activity;

import android.app.Activity;
import android.app.Application;

import com.fenbi.android.leo.LeoApplication;

public class HomeActivity extends Activity {
    private static Application b() {
        return LeoApplication.getInstance();
    }
}
