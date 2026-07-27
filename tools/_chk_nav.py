import re
h = open('site/.vitepress/dist/ja/annihilation.html', encoding='utf-8').read()
m = re.search(r'<header.*?</header>', h, re.S)
nav = m.group(0) if m else ''
# 提取所有 class 含 title 或 trans-title 的标签
for mm in re.finditer(r'<[^>]*class="[^"]*(?:trans-)?title[^"]*"[^>]*>.*?</[^>]*>|<[^>]*class="[^"]*(?:trans-)?title[^"]*"[^>]*>', nav):
    s = mm.group(0)
    if len(s) < 160:
        print(repr(s))
print('----- header 长度', len(nav))
print(nav[:2500])
