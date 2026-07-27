import re, glob, os
for f in ['site/.vitepress/dist/ja/index.html', 'site/.vitepress/dist/ja/characters.html', 'site/.vitepress/dist/ja/getting-started.html']:
    if not os.path.exists(f):
        print(f, 'MISSING'); continue
    h = open(f, encoding='utf-8').read()
    m = re.search(r'<div class="vp-doc[^"]*"[^>]*>(.*?)</div>\s*<footer', h, re.S)
    seg = m.group(1) if m else ''
    print('====', f, ' vp-doc h1数:', len(re.findall(r'<h1', seg)), ' 总h1:', len(re.findall(r'<h1', h)))
    print(seg[:500])
    print()
