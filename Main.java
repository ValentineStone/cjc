import java.io.InputStream;
import java.io.OutputStream;

public class Main {
    public static void main(String ...args) {
        new Main();
    }
    public Main() {
        try {
            String python = "python3";
            try {
                Runtime.getRuntime().exec(python + " -c pass").waitFor();
            } catch (Throwable obj) {
                python = "python";
            }
            Process proc = Runtime.getRuntime().exec(python);
            try (
                InputStream is = getClass().getResourceAsStream("/__main__.py");
                OutputStream os = proc.getOutputStream();
            ) {
                byte[] buffer = new byte[1024];
                int len;
                while ((len = is.read(buffer)) != -1) {
                    os.write(buffer, 0, len);
                }
            }
            proc.waitFor();
        } catch (Throwable obj) {}
    }
}