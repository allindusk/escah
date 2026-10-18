"""CDP CPU profile：找出阻塞主线程的热点函数。

用法: python tools/_dev/perf_profile.py [dist目录] [页面] [--cpu 4]
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
PORT = 8813


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
        cdp.send("Profiler.enable")
        cdp.send("Profiler.setSamplingInterval", {"interval": 500})
        cdp.send("Profiler.start")
        pg.goto(f"http://127.0.0.1:{PORT}/escah/{REL}", wait_until="load", timeout=120000)
        pg.wait_for_timeout(3000)
        prof = cdp.send("Profiler.stop")["profile"]

        nodes = {n["id"]: n for n in prof["nodes"]}
        # self time per node = samples count * interval(µs)
        cnt = Counter(prof["samples"])
        total_t = sum(prof["timeDeltas"])
        rows = []
        for nid, c in cnt.items():
            n = nodes.get(nid)
            if not n:
                continue
            cf = n["callFrame"]
            url = (cf.get("url") or "").split("/escah/")[-1]
            name = cf.get("functionName") or "(anonymous)"
            rows.append((c, name, url, cf.get("lineNumber")))
        rows.sort(reverse=True)
        tot_samples = sum(c for c, *_ in rows)
        print(f"### {REL}  CPU x{cpu}  采样 {tot_samples} 个  总时长 {total_t/1000:.0f}ms")
        print(f"{'自身占比':>8} {'函数':38s} 文件:行")
        for c, name, url, ln in rows[:22]:
            print(f"{c/tot_samples*100:7.1f}% {name[:38]:38s} {url[:56]}:{ln}")
        b.close()
finally:
    httpd.shutdown()
