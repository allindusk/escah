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
    # displayName(正文可能出现的形式：日文名 / 中文名) → 规范化 key(=文件名=modal 加载 key)
    # 正文里中文页会把角色名渲染成 name_zh，必须也映射回日文 key，否则悬停加载会 404。
    name_aliases: dict[str, str] = {}
    for n in names:
        d = json.load(open(os.path.join(CHAR_DIR, n + '.json'), encoding='utf-8'))
        name_aliases[n] = n  # 日文名即 key
        zh = d.get('name_zh', '')
        if zh and zh != n:
            name_aliases[zh] = n
        icon = d.get('icon', '')
        if not icon:
            continue
        # icon 形如 "img/<hash>.png"（本地资源，frag 里即 /img/<hash>）——
        # 直接取其文件名作为 hash 键；少数历史数据为 wiki 原始路径 attach2/<hex>.png，
        # 则经 pending_assets 反查本地 hash。
        if icon.startswith('img/'):
            h = icon.split('/')[-1]
        elif icon.startswith('http'):
            h = pending.get(icon)
        else:
            h = pending.get('https://escalationheroines.wikiru.jp/' + icon)
        if h:
            avatar_hashes[h] = n

    out = {'names': names, 'avatarHashes': avatar_hashes, 'nameAliases': name_aliases}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
    print(f'角色名: {len(names)}  头像hash映射: {len(avatar_hashes)}  别名(含中文名): {len(name_aliases)}  -> {os.path.relpath(OUT, ROOT)}')


if __name__ == '__main__':
    main()
