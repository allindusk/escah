"""站点图片验收：WebP 是否全部能加载（404 / 解码失败 = 0），并报告图片字节数。

用法: python -u tools/_dev/verify_webp_site.py [dist]
"""
import http.server
import socketserver
import sys
import threading
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "site" / ".vitepress" / (sys.argv[1] if len(sys.argv) > 1 else "dist")
PORT = 8850

PAGES = [
    "zh/characters.html",
    "zh/skills.html",
    "zh/equip-067.html",
    "zh/list-ssr.html",
    "zh/bedroom-scenes.html",
    "ja/characters.html",
]


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

JS = """() => {
  const imgs = Array.from(document.images);
  const broken = imgs.filter(i => i.complete && i.naturalWidth === 0).map(i => i.currentSrc || i.src);
  const loaded = imgs.filter(i => i.naturalWidth > 0);
  const webp = loaded.filter(i => /(\\.webp)(\\?|$)/.test(i.currentSrc || i.src)).length;
  const bytes = performance.getEntriesByType('resource')
    .filter(e => e.initiatorType === 'img')
    .reduce((s, e) => s + (e.encodedBodySize || e.transferSize || 0), 0);
  return { total: imgs.length, loaded: loaded.length, webp, broken: broken.slice(0, 5),
           brokenCount: broken.length, imgKB: Math.round(bytes / 1024) };
}"""

total_kb = 0
bad = 0
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="msedge")
        for rel in PAGES:
            ctx = br.new_context(viewport={"width": 1366, "height": 900})
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
            pg.goto(f"http://127.0.0.1:{PORT}/escah/{rel}", wait_until="load", timeout=120000)
            pg.wait_for_timeout(2500)
            # 滚到底触发懒加载
            pg.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            pg.wait_for_timeout(2000)
            d = pg.evaluate(JS)
            total_kb += d["imgKB"]
            bad += d["brokenCount"]
            print(f"{rel:28s} img {d['total']:3d} 已加载 {d['loaded']:3d} (webp {d['webp']:3d}) "
                  f"字节 {d['imgKB']:5d}KB  坏图 {d['brokenCount']}" +
                  (f" {d['broken'][:2]}" if d["brokenCount"] else "") +
                  (f"  页面报错 {errs[:1]}" if errs else ""))
            ctx.close()

        # 角色浮窗头像（走 charRefs.avatarHashes 的 .webp 键）
        ctx = br.new_context(viewport={"width": 1366, "height": 900})
        pg = ctx.new_page()
        pg.goto(f"http://127.0.0.1:{PORT}/escah/zh/characters.html", wait_until="load", timeout=120000)
        pg.wait_for_timeout(2000)
        ref = pg.query_selector(".char-ref")
        if ref:
            ref.scroll_into_view_if_needed()
            box = ref.bounding_box()
            pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            pg.wait_for_timeout(1200)
        modal = pg.evaluate("""() => {
            const m = document.querySelector('.char-modal');
            if (!m) return null;
            const img = m.querySelector('img.char-avatar');
            return { has: true, src: img ? (img.currentSrc || img.src) : '',
                     ok: img ? img.naturalWidth > 0 : null };
        }""")
        print("角色浮窗:", modal)
        ctx.close()
        br.close()
finally:
    httpd.shutdown()

print(f"\n6 页图片合计 {total_kb}KB，坏图总计 {bad} 个")
