import json, re
from pathlib import Path
from bs4 import BeautifulSoup
from copy import deepcopy

d = json.loads(Path('data/parsed/comment_zh.json').read_text(encoding='utf-8'))
dq = d['daily-quest']
dq_cids = set(dq.keys())

ja = BeautifulSoup(Path('data/parsed/ja/daily-quest.html').read_text(encoding='utf-8'), 'lxml')
ja_cids = {}
for li in ja.find_all('li', class_='pcmt'):
    cid = li.get('data-comment-id')
    if not cid:
        continue
    clone = deepcopy(li)
    for ul in clone.find_all('ul'):
        ul.decompose()
    for sp in clone.find_all('span', class_='comment_date'):
        sp.decompose()
    body = clone.get_text(' ').strip()
    body = re.sub(r'\s*(--\s*)?\[[^\]]+\]\s*$', '', body).strip()
    ja_cids[cid] = body

ja_set = set(ja_cids)
print('JA cids 数:', len(ja_set), '| JSON cids 数:', len(dq_cids))
print('\n=== JA 中有但 JSON 缺失（需补译，当前日文）===')
for cid in sorted(ja_set - dq_cids):
    print('  CID:', cid)
    print('     正文:', ja_cids[cid])
print('\n=== JSON 中有但 JA 不存在（phantom，可删）===')
for cid in sorted(dq_cids - ja_set):
    print('  ', cid, '->', repr(dq[cid])[:60])
