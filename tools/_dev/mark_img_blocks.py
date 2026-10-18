"""给存量 i18n JSON 的「块内嵌 <img>」打标（blk["img"] = True），只写这一个字段。

为什么：渲染期 render_locale 为保图片会跳过这类块的块级回退，成员 key 的节点级译文
才是唯一显示源。引擎（extract/统计/进度）必须据此把成员视为「未被块覆盖」，
否则空 zh 的 key 既不进待译队列也不被回填 → 页面静默露日文。

用法： python tools/_dev/mark_img_blocks.py
"""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'pipeline'))
from lxml import html as lxml_html

I18N = Path('data/parsed/i18n')
BLK_ATTR = 'data-i18n-blk'

n_file = n_blk = 0
for f in sorted(I18N.rglob('*.json')):
    tpl = f.with_suffix('.template.html')
    if not tpl.exists():
        continue
    text = tpl.read_text(encoding='utf-8')
    if BLK_ATTR not in text or '<img' not in text:
        continue
    try:
        frag = lxml_html.fragment_fromstring(text, create_parent='div')
        img_bids = {el.get(BLK_ATTR) for el in frag.xpath(f'.//*[@{BLK_ATTR}]')
                    if el.xpath('.//img')}
    except Exception:
        continue
    if not img_bids:
        continue
    d = json.load(open(f, encoding='utf-8'))
    blocks = d.get('_blocks') or {}
    changed = 0
    for bid in img_bids:
        b = blocks.get(bid)
        if b and not b.get('img'):
            b['img'] = True
            changed += 1
    if changed:
        f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
        n_file += 1
        n_blk += changed
print(f'打标完成：{n_blk} 个块 / {n_file} 个页面')
