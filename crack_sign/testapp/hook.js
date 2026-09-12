console.log("[SIGN] frida gadget loaded");

// 解析 libc++ std::string 的 SBO 布局，返回 {len, hex, str}
function readStdString(ptr) {
    var b0 = ptr.readU8();
    var dataPtr, len;
    if (b0 & 1) {
        // heap / long 模式：size 在 +4，data 指针在 +8
        len = ptr.add(4).readU32();
        dataPtr = ptr.add(8).readPointer();
    } else {
        // inline / short 模式：长度 = b0>>1，数据在 +1
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
    console.log("[SIGN] libRequestEncoder base = " + base);

    // MD5 入口 0x43338（Thumb，实际地址 +1）
    var md5 = base.add(0x43338 | 1);
    console.log("[SIGN] hook MD5 @ " + md5);
    Interceptor.attach(md5, {
        onEnter: function (args) {
            // args[0]=r0=输出对象, args[1]=r1=输入 std::string*
            try {
                var s = readStdString(args[1]);
                console.log("[MD5-INPUT] len=" + s.len);
                console.log("[MD5-INPUT] str=" + s.str);
                console.log("[MD5-INPUT] hex=" + s.hex);
            } catch (e) {
                console.log("[MD5-INPUT] read error: " + e);
            }
        },
        onLeave: function (retval) {
            try {
                console.log("[MD5-RESULT] " + hexdump(retval, { length: 16, ansi: false }));
            } catch (e) {
                console.log("[MD5-RESULT] read error: " + e);
            }
        }
    });
}

setTimeout(hookMd5, 300);
