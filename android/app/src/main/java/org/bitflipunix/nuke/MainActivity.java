package org.bitflipunix.nuke;
import android.app.Activity;
import android.os.Bundle;
import android.content.pm.ActivityInfo;
public final class MainActivity extends Activity {
  @Override public void onCreate(Bundle b) {
    super.onCreate(b);
    getWindow().getDecorView().setSystemUiVisibility(5894|1024|512);
    setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE);
    setContentView(new ArenaView(this));
  }
}
