import json, re
html = json.load(open('site/.vitepress/frag/annihilation.ja.json', encoding='utf-8'))['html']
print('--- 前 1400 字 ---')
print(html[:1400])
print('--- 含 h1? ---', bool(re.search(r'<h1', html)))
print('--- 含 title 类? ---', bool(re.search(r'class=.title.', html)))
print('--- 含 jumpmenu? ---', 'jumpmenu' in html)
print('--- 含 anchor_super? ---', 'anchor_super' in html)
print('--- 含 table? ---', bool(re.search(r'<table', html)))
print('--- classList 头 ---', re.findall(r'class=.([^"]+)', html[:1400])[:12])
