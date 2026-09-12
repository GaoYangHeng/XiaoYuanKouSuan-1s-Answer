# NOTE: the capture/sample data this script depends on was removed from the repo. Kept for archive/reference only.
from mitmproxy import io
from mitmproxy.exceptions import FlowReadException

FLOW_FILE = r"f:\traework_main workspace\xiaoyuan-kousuan-re\flows.mitm"

with open(FLOW_FILE, "rb") as fp:
    reader = io.FlowReader(fp)
    try:
        for flow in reader.stream():
            req = flow.request
            if "user-devices" not in req.pretty_url:
                continue
            print("=" * 70)
            print("REQ", req.method, req.pretty_url)
            for k, v in req.headers.items():
                print("  REQH %s: %s" % (k, v))
            if req.content:
                print("  REQBODY(len=%d):" % len(req.content))
                print(req.get_text(strict=False))
            if flow.response:
                resp = flow.response
                print("RESP %s %s" % (resp.status_code, resp.reason))
                for k, v in resp.headers.items():
                    print("  RESPH %s: %s" % (k, v))
                if resp.content:
                    print("  RESPBODY:")
                    print(resp.get_text(strict=False))
    except FlowReadException as e:
        print("end:", e)
