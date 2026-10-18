"""两个 dist 的 DOM 结构对照（验证优化没有改变页面行为）。

用法: python tools/_dev/smoke_compare.py <distA> <distB>
"""
import http.server
import socketserver
import sys
import threading
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "site" / ".vitepress" / sys.argv[1]
B = ROOT / "site" / ".vitepress" / sys.argv[2]
PORT_A, PORT_B = 8820, 8821

PAGES = [
    "zh/",
    "zh/characters.html",
    "zh/list-ssr.html",
    "zh/list-sr.html",
    "zh/list-r.html",
    "zh/list-npc.html",
    "zh/skills.html",
    "zh/getting-started.html",
    "zh/equip-067.html",
    "zh/bedroom-scenes.html",
    "zh/unique-effects.html",
    "zh/raid-001.html",
    "zh/stat-treasure-open.html",
    "ja/characters.html",
    "ja/skills.html",
]

JS = """() => ({
  tbl: document.querySelectorAll('.escah-tbl').length,
  scroll: document.querySelectorAll('.table-scroll').length,
  shrink: document.querySelectorAll('table.escah-tbl-shrink').length,
  chars: document.querySelectorAll('.char-ref').length,
  dataChar: document.querySelectorAll('[data-char]').length,
  filterRow: document.querySelectorAll('.escah-tbl-filter-row').length,
  colgroup: document.querySelectorAll('colgroup col').length,
  sortable: document.querySelectorAll('thead th[data-sort]').length,
  nodes: document.getElementsByTagName('*').length,
  theadH: document.querySelectorAll('.escah-tbl[style], .escah-tbl table[style*="--escah-thead-h"]').length,
  firstColW: (() => { const c = document.querySelector('table.escah-tbl-shrink colgroup col'); return c ? c.style.width : '' })(),
  colW: (() => { const cs = document.querySelectorAll('table.escah-tbl-shrink colgroup col'); return Array.from(cs).slice(0,4).map(c => c.style.width).join('|') })(),
})"""


def serve(dist: Path, port: int):
    class H(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            p = path.split("?")[0]
            if p.startswith("/escah/"):
                p = p[len("/escah/"):]
            return str(dist / p.lstrip("/"))

        def log_message(self, *a):
            pass

    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


from playwright.sync_api import sync_playwright  # noqa: E402

ha = serve(A, PORT_A)
hb = serve(B, PORT_B)
rows = []
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="msedge")
        for rel in PAGES:
            got = {}
            for tag, port in (("A", PORT_A), ("B", PORT_B)):
                ctx = br.new_context(viewport={"width": 1366, "height": 900})
                pg = ctx.new_page()
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
                pg.goto(f"http://127.0.0.1:{port}/escah/{rel}", wait_until="load", timeout=120000)
                pg.wait_for_timeout(1800)
                d = pg.evaluate(JS)
                d["err"] = len(errs)
                got[tag] = d
                if errs:
                    print(f"  !! {tag} {rel} 报错: {errs[:2]}")
                ctx.close()
            rows.append((rel, got["A"], got["B"]))
        br.close()
finally:
    ha.shutdown()
    hb.shutdown()

keys = ["tbl", "scroll", "shrink", "chars", "dataChar", "filterRow", "colgroup", "sortable", "nodes"]
print(f"{'页面':26s} {'指标':10s} {'旧':>8} {'新':>8}  一致")
diff_n = 0
for rel, a, b in rows:
    for k in keys:
        same = a[k] == b[k] or (k == "nodes" and abs(a[k] - b[k]) <= 3)
        if not same:
            diff_n += 1
            print(f"{rel:26s} {k:10s} {a[k]:>8} {b[k]:>8}  ✗")
    if a["err"] or b["err"]:
        print(f"{rel:26s} pageerror 旧={a['err']} 新={b['err']}")
    if a["colW"] != b["colW"]:
        print(f"{rel:26s} colW 旧={a['colW']} 新={b['colW']}  ✗")
print(f"\n共 {len(rows)} 页；不一致指标 {diff_n} 项")
