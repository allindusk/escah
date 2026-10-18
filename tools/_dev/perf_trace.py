"""Chrome DevTools 时间线追踪：把「浏览器内部工作」按类别聚合（布局/样式/解析/绘制/解码）。

用法: python tools/_dev/perf_trace.py [dist] [页面] [--cpu 4]
"""
import http.server
import socketserver
import sys
import threading
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
argv = sys.argv[1:]
cpu = 4
if "--cpu" in argv:
    i = argv.index("--cpu")
    cpu = int(argv[i + 1])
    del argv[i:i + 2]
DIST = ROOT / "site" / ".vitepress" / (argv[0] if argv else "dist")
REL = argv[1] if len(argv) > 1 else "zh/characters.html"
PORT = 8815


class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = path.split("?")[0]
        if p.startswith("/escah/"):
            p = p[len("/escah/"):]
        return str(DIST / p.lstrip("/"))

    def log_message(self, *a):
        pass


from playwright.sync_api import sync_playwright  # noqa: E402

socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), H)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="msedge")
        ctx = b.new_context(viewport={"width": 1366, "height": 900})
        pg = ctx.new_page()
        cdp = ctx.new_cdp_session(pg)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": cpu})
        cdp.send("Tracing.start", {
            "categories": "devtools.timeline,blink.user_timing,v8.execute,disabled-by-default-devtools.timeline",
            "options": "record-as-much-as-possible",
        })
        events_buf = []
        done = {"v": False}

        def on_data(ev):
            events_buf.extend(ev["value"])

        def on_done(ev):
            done["v"] = True

        cdp.on("Tracing.dataCollected", on_data)
        cdp.on("Tracing.tracingComplete", on_done)
        pg.goto(f"http://127.0.0.1:{PORT}/escah/{REL}", wait_until="load", timeout=120000)
        pg.wait_for_timeout(2500)
        cdp.send("Tracing.end")
        for _ in range(600):
            pg.wait_for_timeout(100)
            if done["v"]:
                break
        events = events_buf
        agg = Counter()
        for e in events:
            if e.get("ph") != "X":
                continue
            dur = e.get("dur", 0) / 1000.0
            name = e.get("name")
            if name in ("Layout", "UpdateLayoutTree", "ParseHTML", "Paint", "ImageDecode",
                        "PrePaint", "RecalcStyle", "FunctionCall", "EvaluateScript", "v8.compile",
                        "ImageResize", "RasterTask", "Decode Image", "ResourceSendRequest",
                        "ParseAuthorStyleSheet", "Commit", "Layerize"):
                agg[name] += dur
        total = sum(agg.values())
        print(f"### {REL}  CPU x{cpu}  事件 {len(events)}  归类合计 {total:.0f}ms")
        for k, v in agg.most_common(18):
            print(f"  {v:9.1f}ms  {k}")
        long_js = sorted(
            ((e.get("dur", 0) / 1000.0, e.get("name"), (e.get("args", {}).get("data", {}) or {}).get("url", ""))
             for e in events if e.get("ph") == "X" and e.get("dur", 0) > 200000),
            reverse=True)[:8]
        print("  -- 超过 200ms 的单个事件 --")
        for d, n, u in long_js:
            print(f"  {d:9.1f}ms  {n}  {str(u).split('/escah/')[-1][:50]}")
        b.close()
finally:
    httpd.shutdown()
