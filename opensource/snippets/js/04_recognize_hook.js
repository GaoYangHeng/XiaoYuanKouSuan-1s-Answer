// 片段：劫持识别桥（PK 页核心）
// 说明：前端用 signature_pad 收集笔迹后，通过 JSBridge 调 MathExercise_recognize 让原生识别。
//       抢在原生调用之前命中，直接回传正确答案即可。

(function () {
  function b64d(s) {
    var b = atob(s), u = new Uint8Array(b.length), i;
    for (i = 0; i < b.length; i++) { u[i] = b.charCodeAt(i); }
    return JSON.parse(new TextDecoder().decode(u));
  }
  function b64e(o) {
    var b = new TextEncoder().encode(JSON.stringify(o)), s = '', i;
    for (i = 0; i < b.length; i++) { s += String.fromCharCode(b[i]); }
    return btoa(s);
  }

  // 关键点：目标代码的 Android 分支会优先查找
  //   window[Capitalize(namespace) + "WebView"]   ->  window.MathExerciseWebView
  // 命中即 return，**不再回落** 到 window.LeoWebView.callNative。
  // 因此注入该对象必然被优先使用。
  window.MathExerciseWebView = {
    recognize: function (p) {
      try {
        var a = (b64d(p).arguments || [])[0] || {};
        var ans = a.expectedResult || [];
        var t = a.trigger;

        // 题目未就绪时 expectedResult 为空：吞掉，不回 trigger，避免误判为答错
        if (!t || !ans.length) {
          window.__pkSwallow += 1;
          return true;
        }

        var r = String(ans[0]);
        window.__pkRecv += 1;
        window.__pkCurAns = r;

        // 延迟一小段再回调，模拟真实识别耗时（时间戳需真实）
        var d = 10 + Math.floor(Math.random() * 12);
        setTimeout(function () {
          try {
            if (window[t]) { window[t](b64e([null, r])); }
          } catch (e) { /* 忽略 */ }
        }, d);

        return true;
      } catch (e) {
        return true;
      }
    }
  };
})();

/*
 * 加速切题（可选）
 * ------------------------------------------------------------------
 * 官方在判定答对后有一个 200ms 的切题定时器。识别回调后的短时间内，
 * 把该定时器压到 1ms，可让题目快速切换（题目依然逐道可见）。
 *
 *   var __origST = window.setTimeout;
 *   window.setTimeout = function (fn, ms) {
 *     if (ms === 200 && Date.now() < window.__pkFastUntil) { ms = 1; }
 *     return __origST.call(window, fn, ms);
 *   };
 *
 * 同理，开场 ready-go 的 2000/1000/500ms 计时链也可压缩，并让
 * HTMLMediaElement.prototype.play 对 ready_go 资源直接 resolve 以静音跳过。
 */
