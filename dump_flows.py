# NOTE: the capture/sample data this script depends on was removed from the repo. Kept for archive/reference only.
import sys
from mitmproxy import io
from mitmproxy.exceptions import FlowReadException

FLOW_FILE = r"f:\traework_main workspace\xiaoyuan-kousuan-re\flows.mitm"
OUT_FILE = r"f:\traework_main workspace\xiaoyuan-kousuan-re\flows_dump.txt"

targets = ["xyks.yuanfudao.com", "leo.fbcontent.cn"]

with open(FLOW_FILE, "rb") as fp, open(OUT_FILE, "w", encoding="utf-8") as out:
    reader = io.FlowReader(fp)
    try:
        for flow in reader.stream():
            try:
                req = flow.request
                host = req.pretty_host if hasattr(req, "pretty_host") else ""
                if not any(t in host for t in targets):
                    continue
                url = req.pretty_url
                out.write("=" * 80 + "\n")
                out.write("REQ " + req.method + " " + url + "\n")
                for k, v in req.headers.items():
                    out.write("  REQH %s: %s\n" % (k, v))
                if req.content:
                    body = req.get_text(strict=False)
                    if body:
                        out.write("  REQBODY %s\n" % body[:2000])
                if flow.response:
                    resp = flow.response
                    out.write("RESP %s %s\n" % (resp.status_code, resp.reason))
                    for k, v in resp.headers.items():
                        out.write("  RESPH %s: %s\n" % (k, v))
                    if resp.content:
                        body = resp.get_text(strict=False)
                        if body:
                            out.write("  RESPBODY %s\n" % body[:3000])
            except Exception as e:
                out.write("ERR %s\n" % e)
    except FlowReadException as e:
        print("read end:", e)

print("done ->", OUT_FILE)
