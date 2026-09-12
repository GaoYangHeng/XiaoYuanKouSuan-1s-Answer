package com.yuanfudao.android.leo.stub;

import android.content.ContentResolver;
import android.util.Log;

public final class SecureStub {
    public static String getString(ContentResolver contentResolver, String str) {
        Log.i("SignProbe", "SecureStub.getString key=[" + str + "] resolver=" + (contentResolver == null ? "null" : "ok"));
        return "0123456789abcdef";
    }
}
