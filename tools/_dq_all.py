import re
from pathlib import Path
from bs4 import BeautifulSoup
from copy import deepcopy

raw = Path('data/parsed/ja/daily-quest.html').read_text(encoding='utf-8')
soup = BeautifulSoup(raw, 'lxml')
for li in soup.find_all('li', class_='pcmt'):
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
    print(f'[{cid}]')
    print(f'   {body[:90]}')
