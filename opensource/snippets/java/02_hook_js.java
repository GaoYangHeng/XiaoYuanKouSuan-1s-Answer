// 片段：注入 JS 拦截 XHR / fetch，抓取题目响应
// 说明：题目接口返回加密二进制，需在页面侧截获后交给原生解密。
// 关键：多人（8 人）对局路径为 .../pk/multi/match/v2，**不含** "/pk/match" 子串，必须一并匹配。

public class PkHelper {

    private static final String HOOK_JS =
        "(function () {"
        // 统一出口：t 为响应体；加密二进制会编码成 'AB64:' + base64
        + "var s = function (t) {"
        + "  window.__pkMatchData = t;"
        + "  try {"
        + "    if (window.PkHook) { PkHook.pkMatchCaptured(t); }"
        + "  } catch (e) {}"
        + "};"

        // ---- 拦截 XMLHttpRequest ----
        + "var o = XMLHttpRequest.prototype.open, f0 = XMLHttpRequest.prototype.send;"
        + "XMLHttpRequest.prototype.open = function (m, u) { this.__u = u; return o.apply(this, arguments); };"
        + "XMLHttpRequest.prototype.send = function () {"
        + "  var x = this;"
        + "  x.addEventListener('load', function () {"
        + "    try {"
        // 注意：必须同时匹配 '/multi/match'，否则 8 人局抓不到
        + "      if (x.__u && (x.__u.indexOf('/pk/match') >= 0 || x.__u.indexOf('/multi/match') >= 0)) {"
        + "        var t = null;"
        + "        if (x.responseType === 'arraybuffer' && x.response) {"
        + "          var u = new Uint8Array(x.response), b = '';"
        + "          for (var k = 0; k < u.length; k++) { b += String.fromCharCode(u[k]); }"
        + "          t = 'AB64:' + btoa(b);"
        + "        } else { t = x.responseText; }"
        + "        if (t) { s(t); }"
        + "      }"
        + "    } catch (e) {}"
        + "  });"
        + "  return f0.apply(this, arguments);"
        + "};"

        // ---- 拦截 fetch ----
        + "var f = window.fetch;"
        + "if (f) {"
        + "  window.fetch = function () {"
        + "    var u = (typeof arguments[0] === 'string') ? arguments[0]"
        + "          : ((arguments[0] && arguments[0].url) || '');"
        + "    var p = f.apply(this, arguments);"
        + "    try {"
        + "      if (u && (u.indexOf('/pk/match') >= 0 || u.indexOf('/multi/match') >= 0)) {"
        + "        p.then(function (r) {"
        + "          var ct = (r.headers.get('content-type') || '');"
        + "          if (ct.indexOf('json') >= 0 || ct.indexOf('text') >= 0) {"
        + "            r.clone().text().then(s);"
        + "          } else {"
        + "            r.clone().arrayBuffer().then(function (b) {"
        + "              var u2 = new Uint8Array(b), str = '';"
        + "              for (var k = 0; k < u2.length; k++) { str += String.fromCharCode(u2[k]); }"
        + "              s('AB64:' + btoa(str));"
        + "            });"
        + "          }"
        + "        });"
        + "      }"
        + "    } catch (e) {}"
        + "    return p;"
        + "  };"
        + "}"
        + "})();";
}

/*
 * 配套：判定该响应是"题目"还是"错误"
 * ------------------------------------------------------------------
 * 错误响应是明文 JSON，但走 arraybuffer 分支后会被加上 'AB64:' 前缀，
 * 因此不能只看前缀，需要 base64 解码后判断：
 *
 *   raw = atob(t.substring(5))
 *   ok  = (raw.charAt(0) !== '{')     // '{' => 明文错误(失败)；二进制 => 加密题目(成功)
 *
 * 早先只判断 'AB64:' 前缀就认定为成功，导致匹配失败被误判为成功，重试逻辑不触发。
 */
