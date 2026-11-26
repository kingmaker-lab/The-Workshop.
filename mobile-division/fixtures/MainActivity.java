package lab.workshop.pulsefixture;
import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
public class MainActivity extends Activity {
    private static native int nativeAnswer();
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        String message = "Pulse EXP-006";
        try {
            System.loadLibrary("pulsefixture");
            message += " JNI=" + nativeAnswer();
        } catch (UnsatisfiedLinkError e) {
            message += " (Java only)";
        }
        TextView text = new TextView(this);
        text.setText(message);
        setContentView(text);
    }
}
