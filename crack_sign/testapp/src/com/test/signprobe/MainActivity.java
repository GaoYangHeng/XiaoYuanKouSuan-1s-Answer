package com.test.signprobe;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;
import android.widget.TextView;

import com.fenbi.android.leo.utils.e;

public class MainActivity extends Activity {
    private static final String TAG = "SignProbe";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TextView tv = new TextView(this);
        setContentView(tv);

        StringBuilder sb = new StringBuilder();
        String path = "/leo-game-pk/android/math/pk/match/v2";
        int[] tss = {1788059160, 1788059161, 1788059162, 1788059163, 1788059164, 1788059165, 1788059220, 1788059221, 1788059222, 1788059223};
        for (int ts : tss) {
            try {
                String sign = e.zcvsd1wr2t(path, "wdi4n2t8edr", ts);
                String line = path + " @ " + ts + " -> " + sign;
                sb.append(line).append("\n");
                Log.i(TAG, line);
            } catch (Throwable t) {
                String line = path + " @ " + ts + " ERROR: " + t;
                sb.append(line).append("\n");
                Log.e(TAG, line, t);
            }
        }
        tv.setText(sb.toString());
    }
}
