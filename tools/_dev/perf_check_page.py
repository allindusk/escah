"""检查本地 dist 服务下页面资源是否都能取到（排查 404）。"""
import http.server
import socketserver
import sys
import threading
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "site" / ".vitepress" / (sys.argv[1] if len(sys.argv) > 1 else "dist")
REL = sys.argv[2] if len(sys.argv) > 2 else "zh/skills.html"
PORT = 8814


class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = path.split("?")[0]
        if p.startswith("/escah/"):
            p = p[len("/escah/"):]
        return str(DIST / p.lstrip("/"))

    def log_message(self, fmt, *a):
        sys.stderr.write(f"[srv] {self.command} {self.path} -> {fmt % a}\n")


from playwright.sync_api import sync_playwright  # noqa: E402

socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), H)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="msedge")
        pg = b.new_page()
        bad = []
        pg.on("response", lambda r: bad.append((r.status, r.url)) if r.status >= 400 else None)
        pg.on("console", lambda m: print("console:", m.type, m.text[:120]))
        pg.goto(f"http://127.0.0.1:{PORT}/escah/{REL}", wait_until="load", timeout=60000)
        pg.wait_for_timeout(1500)
        print("bad responses:", bad[:10])
        print("__VP_HASH_MAP__ present:", pg.evaluate("() => !!window.__VP_HASH_MAP__"))
        print("mirror-content children:", pg.evaluate("() => document.querySelectorAll('.mirror-content *').length"))
        print("tables enhanced:", pg.evaluate("() => document.querySelectorAll('.escah-tbl').length"))
        b.close()
finally:
    httpd.shutdown()
