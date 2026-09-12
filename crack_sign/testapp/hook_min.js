console.log("[SIGN] gadget loaded ok");

setTimeout(function() {
    console.log("[SIGN] timeout ok");
    var base = Module.findBaseAddress("libRequestEncoder.so");
    console.log("[SIGN] libRequestEncoder base = " + base);
}, 500);
