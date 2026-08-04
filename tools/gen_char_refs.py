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
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAR_DIR = os.path.join(ROOT, 'data/parsed/characters')
PENDING = os.path.join(ROOT, 'data/pending_assets.json')
NAMES_YAML = os.path.join(ROOT, 'glossary/names.yaml')
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

    # 把 names.yaml 的权威中文名也并入 nameAliases，使中文站正文里的角色中文名
    # 也能触发 data-char 浮窗。仅当该中文名对应的日文原名是真实角色卡 page key 时才并入，
    # 避免给「无角色卡页的称号/必杀技冠名」加浮窗导致点击 404。
    extra = 0
    skipped = 0
    if os.path.exists(NAMES_YAML):
        gloss = yaml.safe_load(open(NAMES_YAML, encoding='utf-8')) or {}
        for ja, zh in (gloss.get('names') or {}).items():
            if not isinstance(ja, str) or not ja:
                continue
            z = zh if isinstance(zh, str) else (zh.get('name_zh') if isinstance(zh, dict) else '')
            if not z or z == ja:
                continue  # 同形不重复映射
            if ja in names:  # 该日文原名本身是角色卡 page key
                if z not in name_aliases:
                    name_aliases[z] = ja
                    extra += 1
            else:
                skipped += 1  # 无角色卡页，跳过（避免浮窗 404）

    out = {'names': names, 'avatarHashes': avatar_hashes, 'nameAliases': name_aliases}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
    print(f'角色名: {len(names)}  头像hash映射: {len(avatar_hashes)}  别名(含中文名): {len(name_aliases)}  (+names.yaml权威中文名 {extra}, 跳过无卡 {skipped})  -> {os.path.relpath(OUT, ROOT)}')


if __name__ == '__main__':
    main()
