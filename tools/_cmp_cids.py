from pathlib import Path
import re
for slug in ['daily-quest', 'prereg-bonus', 'tips']:
    for lang in ['ja', 'zh']:
        p = Path(f'data/parsed/{lang}/{slug}.html')
        t = p.read_text(encoding='utf-8')
        cids = re.findall(r'data-comment-id="([^"]+)"', t)
        has_pcomment = 'pcomment' in t
        print(f'{lang}/{slug}: pcmt数={len(cids)} pcomment块存在={has_pcomment}')
        if slug == 'daily-quest' and lang == 'ja':
            print('   ja cids 前5:', cids[:5])
            print('   ja cids 后3:', cids[-3:])
