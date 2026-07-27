import re
h = open('site/.vitepress/dist/ja/annihilation.html', encoding='utf-8').read()
m = re.search(r'<div class="vp-doc[^"]*"[^>]*>(.*?)</div>\s*<footer', h, re.S)
seg = m.group(1) if m else h
# 找前若干个含 title 类的标签及其前后文
for mm in re.finditer(r'<[^>]*class="[^"]*title[^"]*"[^>]*>.*?</[^>]*>|<[^>]*class="[^"]*title[^"]*"[^>]*>', seg):
    s = mm.group(0)
    if len(s) < 200:
        print(repr(s))
print('----- vp-doc 开头 800 字 -----')
print(seg[:800])
