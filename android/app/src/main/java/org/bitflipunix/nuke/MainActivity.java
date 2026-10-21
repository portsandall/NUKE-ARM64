package org.bitflipunix.nuke;
import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.widget.TextView;
import android.view.Gravity;
public final class MainActivity extends Activity {
    static { System.loadLibrary("nuke_bootstrap"); }
    private static native String nativeStatus();
    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TextView label = new TextView(this);
        label.setBackgroundColor(Color.rgb(12, 19, 25));
        label.setTextColor(Color.rgb(137, 234, 172));
        label.setTextSize(17f);
        label.setPadding(32, 32, 32, 32);
        label.setGravity(Gravity.CENTER);
        label.setText("NUKE-ARM64 — PROOF OF CONCEPT\n\n" + nativeStatus() + "\n\nThis is a native compilation/packaging test, NOT the playable Nuketown port.");
        setContentView(label);
    }
}
