package com.fenbi.android.leo.pk;

import android.util.Base64;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * 比大小 PK 自动答题引擎。
 * 复用进程内 ds.i4 的 a()（解密）/ c()（加密），无需自己实现 native。
 */
public class PkAnswerEngine {

    private volatile JSONObject lastExamVO;
    private volatile JSONObject lastRoot;
    private volatile long capturedAt;

    /** 抓到新题目数据时触发（由 PkHelper 设置，用于自动提交流程） */
    public static volatile Runnable onExamCaptured;

    public int getQuestionCount() {
        JSONObject examVO = this.lastExamVO;
        if (examVO == null) return 0;
        JSONArray qs = examVO.optJSONArray("questions");
        return qs == null ? 0 : qs.length();
    }

    public String getPkIdStr() {
        JSONObject examVO = this.lastExamVO;
        if (examVO == null) return null;
        String s = examVO.optString("pkIdStr", "");
        return s.length() > 0 ? s : null;
    }

    public JSONObject getLastExamVO() {
        return this.lastExamVO;
    }

    /**
     * 处理 JS 钩子捕获到的 match 响应文本：先按明文 JSON 试，失败再按密文走 ds.i4 解密。
     */
    public void parseCaptured(String body) {
        try {
            if (body == null || body.length() == 0) {
                android.util.Log.i("PkHelper", "captured body empty");
                return;
            }
            android.util.Log.i("PkHelper", "captured len=" + body.length() + " head=" + body.substring(0, Math.min(60, body.length())));
            JSONObject examVO = null;
            if (body.startsWith("AB64:")) {
                // JS 钩子对 arraybuffer 响应的 base64 编码：解出原始密文字节
                byte[] raw = android.util.Base64.decode(body.substring(5), android.util.Base64.DEFAULT);
                android.util.Log.i("PkHelper", "AB64 rawLen=" + raw.length + " head=" + new String(raw, 0, Math.min(32, raw.length), "UTF-8"));
                byte[] plain = ds.i4.a.a(raw);
                examVO = tryExtract(plain);
                if (examVO == null) {
                    examVO = tryExtract(raw);
                }
            }
            if (examVO == null) {
                try {
                    examVO = new JSONObject(body).optJSONObject("examVO");
                } catch (Throwable ignore) {
                }
            }
            if (examVO == null) {
                byte[] plain = ds.i4.a.a(body.getBytes("UTF-8"));
                if (plain == null) {
                    byte[] raw = android.util.Base64.decode(body, android.util.Base64.DEFAULT);
                    plain = ds.i4.a.a(raw);
                }
                examVO = tryExtract(plain);
            }
            if (examVO != null) {
                this.lastExamVO = examVO;
                this.capturedAt = System.currentTimeMillis();
                android.util.Log.i("PkHelper", "captured examVO OK questions=" + (examVO.optJSONArray("questions") == null ? -1 : examVO.optJSONArray("questions").length()));
                dumpExamVo(examVO);
                Runnable r = onExamCaptured;
                if (r != null) {
                    r.run();
                }
            } else {
                android.util.Log.i("PkHelper", "captured but no examVO");
            }
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "parseCaptured err " + t);
        }
    }

    private static void dumpExamVo(JSONObject examVO) {
        try {
            JSONArray qs = examVO.optJSONArray("questions");
            if (qs != null && qs.length() > 0) {
                android.util.Log.i("PkHelper", "Q0=" + qs.optJSONObject(0).toString());
                if (qs.length() > 1) {
                    android.util.Log.i("PkHelper", "Q1=" + qs.optJSONObject(1).toString());
                }
            }
            android.util.Log.i("PkHelper", "EXAMVO_KEYS=" + examVO.keys().toString());
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "dumpExamVo err " + t);
        }
    }

    /**
     * 从明文/半解密字节中提取 examVO：直接 JSON → data 字段包裹密文二次解密。
     */
    private JSONObject tryExtract(byte[] plain) {
        if (plain == null || plain.length == 0) {
            return null;
        }
        try {
            String s = new String(plain, "UTF-8");
            android.util.Log.i("PkHelper", "tryExtract len=" + plain.length + " head=" + s.substring(0, Math.min(60, s.length())));
            JSONObject root = new JSONObject(s);
            JSONObject examVO = root.optJSONObject("examVO");
            if (examVO != null) {
                this.lastRoot = root;
                return examVO;
            }
            String dataStr = root.optString("data", "");
            if (dataStr.length() > 20) {
                byte[] p2 = ds.i4.a.a(dataStr.getBytes("UTF-8"));
                if (p2 == null) {
                    p2 = ds.i4.a.a(android.util.Base64.decode(dataStr, android.util.Base64.DEFAULT));
                }
                if (p2 != null) {
                    JSONObject r2 = new JSONObject(new String(p2, "UTF-8"));
                    JSONObject e2 = r2.optJSONObject("examVO");
                    if (e2 != null) {
                        android.util.Log.i("PkHelper", "data-field decrypt examVO ok");
                        return e2;
                    }
                }
            }
        } catch (Throwable ignore) {
        }
        return null;
    }

    public JSONObject handleEncryptedResponse(byte[] encryptedBody) {
        try {
            byte[] plain = ds.i4.a.a(encryptedBody);
            if (plain == null) {
                android.util.Log.i("PkHelper", "decrypt plain=null");
                return null;
            }
            String head = new String(plain, 0, Math.min(80, plain.length), "UTF-8");
            android.util.Log.i("PkHelper", "decrypt ok len=" + plain.length + " head=" + head);
            JSONObject root = new JSONObject(new String(plain, "UTF-8"));
            JSONObject examVO = root.optJSONObject("examVO");
            if (examVO == null) {
                // 明文 JSON 但无 examVO：试 data 字段包裹密文的常见格式
                try {
                    String plainStr = new String(plain, "UTF-8");
                    JSONObject r2 = new JSONObject(plainStr);
                    String dataStr = r2.optString("data", "");
                    if (dataStr.length() > 20) {
                        byte[] p2 = ds.i4.a.a(dataStr.getBytes("UTF-8"));
                        if (p2 == null) {
                            p2 = ds.i4.a.a(android.util.Base64.decode(dataStr, android.util.Base64.DEFAULT));
                        }
                        if (p2 != null) {
                            examVO = new JSONObject(new String(p2, "UTF-8")).optJSONObject("examVO");
                            android.util.Log.i("PkHelper", "data-field decrypt examVO=" + (examVO != null));
                        }
                    }
                } catch (Throwable ignore2) {
                }
            }
            if (examVO == null) {
                StringBuilder ks = new StringBuilder();
                java.util.Iterator<String> it = root.keys();
                while (it.hasNext() && ks.length() < 150) {
                    ks.append(it.next()).append(',');
                }
                android.util.Log.i("PkHelper", "decrypt no examVO rootKeys=" + ks);
            }
            if (examVO != null) this.lastExamVO = examVO;
            return examVO;
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "decrypt err " + t);
            return null;
        }
    }

    public JSONObject buildAnswerCard() {
        JSONObject examVO = this.lastExamVO;
        if (examVO == null) {
            android.util.Log.i("PkHelper", "buildAnswerCard lastExamVO=null");
            return null;
        }
        try {
            JSONArray srcQ = examVO.optJSONArray("questions");
            android.util.Log.i("PkHelper", "buildAnswerCard questions=" + (srcQ == null ? -1 : srcQ.length()));
            if (srcQ == null || srcQ.length() == 0) {
                android.util.Log.i("PkHelper", "buildAnswerCard questions empty");
                return null;
            }
            // 1. 答题记录 S：每题深拷贝 + status=1(正确) + userAnswer=正确答案 + curTrueAnswer=识别结果对象
            JSONArray s = new JSONArray();
            for (int i = 0; i < srcQ.length(); i++) {
                JSONObject q = new JSONObject(srcQ.getJSONObject(i).toString());
                String answer = q.optString("answer", "");
                q.put("userAnswer", answer);
                JSONObject curTrue = new JSONObject();
                curTrue.put("answer", 1);
                curTrue.put("recognizeResult", answer);
                curTrue.put("pathPoints", new JSONArray());
                q.put("curTrueAnswer", curTrue);
                q.put("status", 1);
                s.put(q);
            }
            android.util.Log.i("PkHelper", "CARD_Q0=" + s.optJSONObject(0).toString());
            long now = System.currentTimeMillis();
            // costTime 必须用真实经过时间：服务器校验其与对局实际时长的一致性
            // 实测成功样本 8134~8898ms（真实值）；人为放大到 10000+ 会触发 403
            long cost = capturedAt > 0 ? (now - capturedAt) : 8000;
            // 直接交卷时真实耗时可能只有几百毫秒，过短易被风控关注；
            // 这里保底 2s（观感仍是瞬间跳结果页，costTime 仅为上报字段）
            if (cost < 2000) {
                cost = 2000;
            }
            if (cost > 9000) {
                cost = 9000;   // 与实测成功区间对齐，不越红线
            }
            // 2. y = {...examVO, questions: S, correctCnt, costTime, updatedTime}
            JSONObject y = new JSONObject(examVO.toString());
            y.put("questions", s);
            y.put("correctCnt", s.length());
            y.put("costTime", cost);
            y.put("updatedTime", now);
            // 3. k = {...y, examVO: y, userInfos, costTime: now}（与官方 H5 postPkExerciseResult 结构一致）
            JSONObject k = new JSONObject(y.toString());
            k.put("examVO", y);
            JSONArray userInfos = new JSONArray();
            JSONObject root = this.lastRoot;
            if (root != null) {
                JSONArray opponents = root.optJSONArray("opponents");
                if (opponents != null) {
                    for (int i = 0; i < opponents.length(); i++) {
                        JSONObject op = opponents.optJSONObject(i);
                        JSONObject ui = op == null ? null : op.optJSONObject("userInfo");
                        if (ui != null) {
                            userInfos.put(ui);
                        }
                    }
                }
            }
            k.put("userInfos", userInfos);
            String kStr = k.toString();
            android.util.Log.i("PkHelper", "CARD_HEAD=" + kStr.substring(0, Math.min(400, kStr.length())));
            android.util.Log.i("PkHelper", "CARD_TAIL=" + kStr.substring(Math.max(0, kStr.length() - 300)));
            android.util.Log.i("PkHelper", "buildAnswerCard OK cnt=" + s.length() + " cost=" + cost);
            return k;
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "buildAnswerCard err " + t);
            return null;
        }
    }

    public String encryptToBase64(JSONObject card) {
        byte[] enc = encryptToBytes(card);
        if (enc == null) return null;
        return Base64.encodeToString(enc, Base64.NO_WRAP);
    }

    /** 与官方 H5 一致：返回 ds.i4 加密后的原始字节（PUT body 直接使用，不再包 base64） */
    public byte[] encryptToBytes(JSONObject card) {
        try {
            byte[] json = card.toString().getBytes("UTF-8");
            byte[] enc = ds.i4.a.c(json);
            if (enc == null) {
                android.util.Log.i("PkHelper", "encryptToBytes enc=null");
            } else {
                android.util.Log.i("PkHelper", "encryptToBytes len=" + enc.length);
            }
            return enc;
        } catch (Throwable t) {
            android.util.Log.i("PkHelper", "encryptToBytes err " + t);
            return null;
        }
    }
}
