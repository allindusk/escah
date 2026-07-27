import re
from pathlib import Path
raw = Path('data/parsed/ja/daily-quest.html').read_text(encoding='utf-8')
# 找到所有 li.pcmt 块及其 cid 和正文(粗略)
for m in re.finditer(r'<li class="pcmt"[^>]*data-comment-id="([^"]+)"[^>]*>(.*?)</li>', raw, re.S):
    cid = m.group(1)
    inner = m.group(2)
    text = re.sub(r'<[^>]+>', ' ', inner)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s*(--\s*)?\[[^\]]+\]\s*$', '', text).strip()
    if 'ありがとう' in text or 'この動画' in text:
        print('CID:', cid)
        print('  正文:', text)
