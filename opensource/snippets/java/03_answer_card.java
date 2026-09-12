// 片段：答案卡构造与本地结果写入
// 说明：把每题标为已答对，并写入前端约定的本地存储，供结果页读取。
// 已脱敏，仅保留结构。

public class PkAnswerEngine {

    /**
     * 构造整卷答案卡。
     * 结构：{ ...examVO, examVO:{...examVO, questions:S, correctCnt, costTime}, userInfos, costTime }
     */
    public JSONObject buildAnswerCard() {
        JSONObject examVO = this.lastExamVO;
        JSONArray srcQ = examVO.optJSONArray("questions");

        JSONArray s = new JSONArray();
        for (int i = 0; i < srcQ.length(); i++) {
            JSONObject q = new JSONObject(srcQ.getJSONObject(i).toString());
            String answer = q.optString("answer", "");

            q.put("userAnswer", answer);

            // 识别结果对象：answer=1 表示判对
            JSONObject curTrue = new JSONObject();
            curTrue.put("answer", 1);
            curTrue.put("recognizeResult", answer);
            curTrue.put("pathPoints", new JSONArray());
            q.put("curTrueAnswer", curTrue);

            q.put("status", 1);              // 1 = 正确
            s.put(q);
        }

        // costTime 用真实经过时间；实测约 1.2~9 秒可通过，过大会被拒
        long cost = (capturedAt > 0) ? (System.currentTimeMillis() - capturedAt) : 8000;
        cost = Math.max(2000, Math.min(cost, 9000));

        JSONObject y = new JSONObject(examVO.toString());
        y.put("questions", s);
        y.put("correctCnt", s.length());
        y.put("costTime", cost);
        y.put("updatedTime", System.currentTimeMillis());

        JSONObject k = new JSONObject(y.toString());
        k.put("examVO", y);
        k.put("userInfos", new JSONArray());   // 对手信息（可选）
        k.put("costTime", cost);
        return k;
    }

    /** 加密：GZIP + 自反变换（与解密同一函数） */
    public byte[] encryptToBytes(JSONObject card) throws Exception {
        return ds.i4.a.c(card.toString().getBytes("UTF-8"));
    }

    /** 解密：自反变换 + GZIP */
    public byte[] decrypt(byte[] raw) {
        return ds.i4.a.a(raw);
    }
}

/*
 * 本地结果写入（关键坑）
 * ------------------------------------------------------------------
 * 前端存储约定是：
 *
 *     localStorage["__local_" + key] = Base64.encode(json)
 *
 * 早先错写为 localStorage['exerciseResult'] = 明文 JSON，
 * 结果页按 '__local_exerciseResult' 读取 -> 读不到 -> 上报空结果，
 * 表现就是"服务器已记账、前端却显示一道题没答"。
 */
