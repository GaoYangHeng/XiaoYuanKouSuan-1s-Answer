package okhttp3;

public class RequestBody {
    public static RequestBody create(MediaType type, String content) { return null; }

    public static RequestBody create(MediaType type, byte[] content) { return null; }

    public MediaType contentType() { return null; }

    public long contentLength() { return -1; }

    public void writeTo(okio.BufferedSink sink) { }
}
