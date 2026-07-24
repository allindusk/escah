import re, pathlib, ast, html, sys, json

slug = sys.argv[1]
src = pathlib.Path(f'data/parsed/ja/{slug}.html')
text = src.read_text(encoding='utf-8')

# 现有键
tree = ast.parse(pathlib.Path('tools/zh_patch.py').read_text(encoding='utf-8'))
existing = set()
def collect(node):
    if isinstance(node.value, ast.Dict):
        for k in node.value.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                existing.add(k.value)
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == 'JA2ZH':
                collect(node)
    elif isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name) and node.target.id == 'JA2ZH':
            collect(node)

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
