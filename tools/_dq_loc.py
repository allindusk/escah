import re
from pathlib import Path
raw = Path('data/parsed/zh/daily-quest.html').read_text(encoding='utf-8')
# 匹配每个 li.pcmt 块（非贪婪，叶子回复能正确截断）
blocks = re.findall(r'<li class="pcmt"[^>]*data-comment-id="([^"]+)"[^>]*>(.*?)</li>', raw, re.S)
for cid, inner in blocks:
    text = re.sub(r'<[^>]+>', ' ', inner)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s*(--\s*)?\[[^\]]+\]\s*$', '', text).strip()
    if 'ありがとう' in text or 'この動画' in text:
        print('CID:', cid)
        print('  正文:', text)
