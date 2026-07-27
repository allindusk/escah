import json, re
from pathlib import Path
from bs4 import BeautifulSoup
from copy import deepcopy

raw = Path('data/parsed/zh/daily-quest.html').read_text(encoding='utf-8')
d = json.loads(Path('data/parsed/comment_zh.json').read_text(encoding='utf-8'))
dq = d['daily-quest']

soup = BeautifulSoup(raw, 'lxml')
for parent_cid in ['comment_a9e7ca649c6c092181cd22ebac5a8895']:
    parent = soup.find('li', class_='pcmt', attrs={'data-comment-id': parent_cid})
    def show(li, depth=0):
        cid = li.get('data-comment-id')
        clone = deepcopy(li)
        for ul in clone.find_all('ul'):
            ul.decompose()
        for sp in clone.find_all('span', class_='comment_date'):
            sp.decompose()
        txt = clone.get_text(' ').strip()
        txt = re.sub(r'\s*(--\s*)?\[[^\]]+\]\s*$', '', txt).strip()
        print('  '*depth + f'[{cid}] JSON有={cid in dq} 正文={txt[:70]}')
    show(parent, 0)
    for nested in parent.find_all('li', class_='pcmt'):
        if nested is parent:
            continue
        show(nested, 1)
