import json, re
from pathlib import Path
raw = Path('data/parsed/ja/daily-quest.html').read_text(encoding='utf-8')
d = json.loads(Path('data/parsed/comment_zh.json').read_text(encoding='utf-8'))
dq = d['daily-quest']

# 提取某 cid 的 li.pcmt 块正文（非贪婪，适合无内嵌 li 的叶子回复）
def body_of(cid):
    m = re.search(r'<li class="pcmt"[^>]*data-comment-id="' + re.escape(cid) + r'"[^>]*>(.*?)</li>', raw, re.S)
    if not m:
        return None
    inner = m.group(1)
    text = re.sub(r'<[^>]+>', ' ', inner)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s*(--\s*)?\[[^\]]+\]\s*$', '', text).strip()
    return text

# 找出所有 ja 中、但 JSON 缺失的 daily-quest cid（含嵌套）
cids = re.findall(r'data-comment-id="(comment_[^"]+)"', raw)
for cid in sorted(set(cids)):
    if cid not in dq:
        print('缺失 CID:', cid)
        print('  正文:', body_of(cid))
