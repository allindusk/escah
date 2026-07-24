#!/usr/bin/env python3
"""生成前端角色引用表 charRefs.json，供 MirrorContent 在全页面绑定角色浮窗。

输出（site/.vitepress/theme/charRefs.json）：
  names        : 全部角色名（= data/parsed/characters/<名>.json 的文件名，亦为 modal 加载 key）
  avatarHashes : { "<img hash 含扩展名>": "<角色名>" } 由角色 icon 字段反查 pending_assets 得到

凡正文里出现这些角色名（纯文本/链接）或头像（/img/<hash>）的地方，
MirrorContent 都会打 data-char 标记并接入悬停展示 / 点击固定浮窗。
"""
import json
import os
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAR_DIR = os.path.join(ROOT, 'data/parsed/characters')
PENDING = os.path.join(ROOT, 'data/pending_assets.json')
OUT = os.path.join(ROOT, 'site/.vitepress/theme/charRefs.json')


def main():
    names = [os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(CHAR_DIR, '*.json'))]
    names = sorted(set(names))

    pending = json.load(open(PENDING, encoding='utf-8'))
    avatar_hashes: dict[str, str] = {}
    for n in names:
        d = json.load(open(os.path.join(CHAR_DIR, n + '.json'), encoding='utf-8'))
        icon = d.get('icon', '')
        if not icon:
            continue
        url = 'https://escalationheroines.wikiru.jp/' + icon  # icon 形如 attach2/<hex>.png
        h = pending.get(url)
        if h:
            avatar_hashes[h] = n

    out = {'names': names, 'avatarHashes': avatar_hashes}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
    print(f'角色名: {len(names)}  头像hash映射: {len(avatar_hashes)}  -> {os.path.relpath(OUT, ROOT)}')


if __name__ == '__main__':
    main()
