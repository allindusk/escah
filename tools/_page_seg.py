import re, pathlib, ast, html, sys, json

slug = sys.argv[1]
src = pathlib.Path(f'data/parsed/ja/{slug}.html')
text = src.read_text(encoding='utf-8')

# 现有键：以用户手工译文 (_manual_zh.json) 为准（原硬编码 JA2ZH 散文词典已于 2026-07-26 移除）。
import json as _json
_manual_file = pathlib.Path('tools/_manual_zh.json')
existing = set()
if _manual_file.is_file():
    try:
        existing = set(_json.loads(_manual_file.read_text(encoding='utf-8')).keys())
    except Exception:
        existing = set()

ka = re.compile(r'[぀-ゟ゠-ヺ]')
tag = re.compile(r'<[^>]+>')

def nodes(s):
    s = tag.sub('\n', s)
    s = html.unescape(s)
    out = []
    for line in s.split('\n'):
        line = line.strip()
        if line and ka.search(line):
            out.append(line)
    return out

counts = {}
for nd in nodes(text):
    if nd in existing:
        continue
    if len(nd) < 2 or len(nd) > 220:
        continue
    counts[nd] = counts.get(nd, 0) + 1

rows = sorted(counts.items(), key=lambda x: (-x[1], -len(x[0])))
out = [f"{i}\t{c}\t{len(s)}\t{s}" for i, (s, c) in enumerate(rows[:200], 1)]
pathlib.Path(f'tools/_seg_{slug}.txt').write_text('\n'.join(out), encoding='utf-8')
print(f"{slug}: candidates={len(rows)} -> tools/_seg_{slug}.txt (top200)")
