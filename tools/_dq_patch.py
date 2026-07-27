import json
from pathlib import Path

P = Path('data/parsed/comment_zh.json')
d = json.loads(P.read_text(encoding='utf-8'))
dq = d['daily-quest']

REPL = {
    'リセットストラップ': '重置表带',
    'チケット': '票券',
    'チューイングガム': '口香糖',
    '円玉': '圆玉',
    'エテ公': '猴子',
}
# ツカサ(角色名)、ちょっといいふとん 氏(YouTuber) 按规则保留日文，不替换

changed = 0
for cid, zh in dq.items():
    new = zh
    for jp, cn in REPL.items():
        if jp in new:
            new = new.replace(jp, cn)
            changed += 1
    dq[cid] = new

P.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
print('应用替换次数:', changed)
print('daily-quest 条目数:', len(dq))
# 打印仍含假名的条目
import re
KANA = re.compile(r'[぀-ゟ゠-ヿ]')
left = [(c, v) for c, v in dq.items() if KANA.search(v)]
print('仍含假名条目数:', len(left))
for c, v in left:
    print('  ', c, '=>', v)
