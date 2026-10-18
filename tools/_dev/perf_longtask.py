"""深入看长任务清单（判断是否主线程阻塞 + 发生在哪个时间点）。

用法: python tools/_dev/perf_longtask.py [dist目录] [页面] [--cpu 4] [--hwmobile]
"""
import http.server
import socketserver
import sys
import threading
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
PAGES = argv[1:] or ["zh/characters.html"]
PORT = 8812

INIT = r"""
(() => {
  window.__lt = [];
  new PerformanceObserver((l) => {
    for (const e of l.getEntries()) {
      window.__lt.push({ s: Math.round(e.startTime), d: Math.round(e.duration), n: e.name,
                         attr: (e.attribution||[]).map(a => a.name + ':' + a.containerType).join(',') });
    }
  }).observe({ entryTypes: ['longtask'] });
})();
"""


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
        for rel in PAGES:
            ctx = b.new_context(viewport={"width": 1366, "height": 900})
            ctx.add_init_script(INIT)
            pg = ctx.new_page()
            cdp = ctx.new_cdp_session(pg)
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": cpu})
            msgs = []
            pg.on("console", lambda m: msgs.append(m.text))
            pg.goto(f"http://127.0.0.1:{PORT}/escah/{rel}", wait_until="load", timeout=120000)
            pg.wait_for_timeout(3000)
            lt = pg.evaluate("() => window.__lt")
            total = sum(x["d"] for x in lt)
            print(f"\n### {rel} (CPU x{cpu})  长任务 {len(lt)} 个 合计 {total}ms")
            for x in lt[:15]:
                print(f"   start {x['s']:6d}ms  持续 {x['d']:6d}ms  {x['n']} {x['attr']}")
            if len(lt) > 15:
                print(f"   ... 其余 {len(lt)-15} 个")
            print("   console:", msgs[:6])
            ctx.close()
        b.close()
finally:
    httpd.shutdown()
