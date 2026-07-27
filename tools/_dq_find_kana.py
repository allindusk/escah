import json, re
from pathlib import Path
d = json.loads(Path('data/parsed/comment_zh.json').read_text(encoding='utf-8'))
dq = d['daily-quest']
KANA = re.compile(r'[぀-ゟ゠-ヿ]')
print('daily-quest 条目数:', len(dq))
for cid, zh in dq.items():
    if KANA.search(zh):
        print('--- 含假名 cid:', cid)
        print('    内容:', zh)
