import frida
import sys

JS = r"""
function readStdString(ptr) {
    var b0 = ptr.readU8();
    var dataPtr, len;
    if (b0 & 1) {
        len = ptr.add(4).readU32();
        dataPtr = ptr.add(8).readPointer();
    } else {
        len = b0 >> 1;
        dataPtr = ptr.add(1);
    }
    if (len > 4096) len = 4096;
    var bytes = dataPtr.readByteArray(len);
    var arr = new Uint8Array(bytes);
    var hex = "";
    var str = "";
    for (var i = 0; i < arr.length; i++) {
        hex += ("0" + arr[i].toString(16)).slice(-2);
        var c = arr[i];
        str += (c >= 32 && c < 127) ? String.fromCharCode(c) : ".";
    }
    return { len: len, hex: hex, str: str };
}

function hookMd5() {
    var base = Module.findBaseAddress("libRequestEncoder.so");
    if (!base) {
        setTimeout(hookMd5, 200);
        return;
    }
    send({t:"base", base: base.toString()});
    var md5 = base.add(0x43338 | 1);
    Interceptor.attach(md5, {
        onEnter: function(args) {
            try {
                var s = readStdString(args[1]);
                send({t:"md5_in", len: s.len, str: s.str, hex: s.hex});
            } catch(e) {
                send({t:"md5_in_err", err: String(e)});
            }
        },
        onLeave: function(retval) {
            try {
                var out = readStdString(args[0]);
                send({t:"md5_out", len: out.len, hex: out.hex});
            } catch(e) {
                send({t:"md5_out_err", err: String(e)});
            }
        }
    });
}

setTimeout(hookMd5, 100);
"""

def on_message(msg, data):
    if msg["type"] == "send":
        p = msg["payload"]
        t = p.get("t")
        if t == "base":
            print("[base]", p["base"])
        elif t == "md5_in":
            print("[MD5-IN] len=%d str=%s" % (p["len"], p["str"]))
            print("         hex=%s" % p["hex"])
        elif t == "md5_out":
            print("[MD5-OUT] len=%d hex=%s" % (p["len"], p["hex"]))
        else:
            print("[%s]" % t, p)
    elif msg["type"] == "error":
        print("[error]", msg["description"])

dev = frida.get_device_manager().add_remote_device("127.0.0.1:27042")
session = dev.attach("com.test.signprobe")
script = session.create_script(JS)
script.on("message", on_message)
script.load()
print("[loaded]")
sys.stdin.read()
