"""用真浏览器测量构建产物（dist_* 目录）的加载与主线程耗时。

用法: python tools/_dev/perf_measure.py [dist目录名] [页1 页2 ...]
"""
import http.server
import socketserver
import sys
import threading
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
args = [a for a in sys.argv[1:] if not a.startswith("--")]
DIST = ROOT / "site" / ".vitepress" / (args[0] if args else "dist")
PAGES = args[1:] or [
    "zh/",
    "zh/characters.html",
    "zh/getting-started.html",
    "zh/equip-067.html",
    "zh/skills.html",
]
CPU = 4
PORT = 8811

INIT_JS = r"""
(() => {
  window.__perf = { longtasks: 0, longtaskMax: 0, lcp: 0, cls: 0, lcpEl: '' };
  try {
    new PerformanceObserver((l) => {
      for (const e of l.getEntries()) {
        window.__perf.longtasks += e.duration;
        window.__perf.longtaskMax = Math.max(window.__perf.longtaskMax, e.duration);
      }
    }).observe({ entryTypes: ['longtask'] });
  } catch (e) {}
  try {
    new PerformanceObserver((l) => {
      const es = l.getEntries();
      const e = es[es.length - 1];
      window.__perf.lcp = e.startTime;
      window.__perf.lcpEl = (e.element && (e.element.tagName + '.' + e.element.className)) || e.url || '';
    }).observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (e) {}
  try {
    new PerformanceObserver((l) => {
      for (const e of l.getEntries()) if (!e.hadRecentInput) window.__perf.cls += e.value;
    }).observe({ type: 'layout-shift', buffered: true });
  } catch (e) {}
})();
"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = path.split("?")[0]
        if p.startswith("/escah/"):
            p = p[len("/escah/"):]
        elif p == "/escah":
            p = ""
        return str(DIST / p.lstrip("/"))

    def log_message(self, *a):
        pass


from playwright.sync_api import sync_playwright  # noqa: E402


def main():
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="msedge")
            for page_rel in PAGES:
                ctx = browser.new_context(viewport={"width": 1366, "height": 900})
                ctx.add_init_script(INIT_JS)
                page = ctx.new_page()
                cdp = ctx.new_cdp_session(page)
                cdp.send("Network.enable")
                cdp.send("Emulation.setCPUThrottlingRate", {"rate": CPU})
                reqs = {}
                rid2url = {}

                def on_sent(ev):
                    r = ev["request"]
                    rid2url[ev["requestId"]] = r["url"]
                    if ev.get("type") in ("Script", "Stylesheet"):
                        it = ev.get("initiator") or {}
                        st = it.get("stack") or {}
                        caller = (st.get("callFrames") or [{}])[0].get("url", "")
                        reqs.setdefault(r["url"], {"type": ev.get("type"), "enc": 0, "ref": ""})
                        reqs[r["url"]]["ref"] = caller.split("/escah/")[-1][:60]

                def on_fin(ev):
                    u = rid2url.get(ev["requestId"])
                    if u and u in reqs:
                        reqs[u]["enc"] = ev.get("encodedDataLength", 0)

                def on_resp(ev):
                    u = ev["response"].get("url", "")
                    if u in reqs:
                        reqs[u]["status"] = ev["response"].get("status")

                cdp.on("Network.requestWillBeSent", on_sent)
                cdp.on("Network.loadingFinished", on_fin)
                cdp.on("Network.responseReceived", on_resp)

                page.goto(f"http://127.0.0.1:{PORT}/escah/{page_rel}", wait_until="load", timeout=120000)
                page.wait_for_timeout(2000)
                m = page.evaluate("() => window.__perf")
                nav = page.evaluate(
                    "() => { const n = performance.getEntriesByType('navigation')[0];"
                    " return { ttfb: n.responseStart, dcl: n.domContentLoadedEventEnd,"
                    " load: n.loadEventEnd, domInt: n.domInteractive }; }"
                )
                img = page.evaluate(
                    "() => { const a = performance.getEntriesByType('resource').filter(r => r.initiatorType==='img');"
                    " return { n: a.length, bytes: a.reduce((s,r)=>s+r.transferSize,0) }; }"
                )
                nodes = page.evaluate("() => document.getElementsByTagName('*').length")
                scripts = sorted(reqs.items(), key=lambda kv: -kv[1]["enc"])
                tot = sum(v["enc"] for v in reqs.values())
                print(f"\n### {page_rel}   (CPU x{CPU})")
                print(f"  FCP/LCP {m['lcp']:.0f}ms (LCP元素 {m['lcpEl'][:60]})  TTFB {nav['ttfb']:.0f}ms"
                      f"  DOMInteractive {nav['domInt']:.0f}ms  Load {nav['load']:.0f}ms  CLS {m['cls']:.3f}")
                print(f"  长任务合计 {m['longtasks']:.0f}ms (最长 {m['longtaskMax']:.0f}ms)  DOM {nodes} 节点"
                      f"  图片 {img['n']} 张 {img['bytes']/1024:.0f}KB")
                print(f"  JS/CSS 请求 {len(scripts)} 个 合计 {tot/1024:.0f}KB（未压缩，含预取）")
                for u, v in scripts[:10]:
                    print(f"    {v['enc']/1024:7.0f}KB {v.get('type','?'):10s} {u.split('/escah/')[-1][:52]:52s} ← {v['ref']}")
                ctx.close()
            browser.close()
    finally:
        httpd.shutdown()


main()
