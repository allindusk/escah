import re, glob, os
for f in ['site/.vitepress/dist/ja/index.html', 'site/.vitepress/dist/ja/annihilation.html']:
    if not os.path.exists(f):
        print(f, 'MISSING'); continue
    h = open(f, encoding='utf-8').read()
    h1s = re.findall(r'<h1[^>]*>', h)
    titles = re.findall(r'class="([^"]*title[^"]*)"', h)
    print('===', f)
    print('  h1 标签数:', len(h1s), h1s[:4])
    print('  class含title的元素:', titles[:6])
