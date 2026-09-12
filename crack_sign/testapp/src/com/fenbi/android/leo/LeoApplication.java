package com.fenbi.android.leo;

import android.app.Application;

public class LeoApplication extends Application {
    private static LeoApplication instance;

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
    }

    public static LeoApplication getInstance() {
        return instance;
    }
}
