# -*- coding: utf-8 -*-
"""全站角色名一致性体检（只读，不改数据）。

检查三类问题：
  A. 生成表与手工表冲突：同一日文名两处译法不同
  B. 同一基名的形态译法不含基名（生成器已保证，这里复查手工覆盖是否破坏）
  C. 页面渲染里出现「假名+中文」混排的半截名（如 レガ莉亚）
用法：python tools/check_char_names.py [--render]
"""
import json, re, sys, yaml
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]


def load(f, sec=None):
    d = yaml.safe_load((ROOT / f).read_text(encoding='utf-8')) or {}
    if sec:
        d = d.get(sec) or {}
    return {k: v for k, v in d.items() if isinstance(k, str) and isinstance(v, str) and k and v and k != v}


gen = load('glossary/characters_generated.yaml', 'names')
man = load('glossary/names.yaml', 'names')
cfg = yaml.safe_load((ROOT / 'glossary' / 'characters.yaml').read_text(encoding='utf-8'))
base = cfg.get('base') or {}
print(f'生成表 {len(gen)} 条 / 手工表 {len(man)} 条 / 基名 {len(base)} 条')

print('\n=== A. 生成表 vs 手工表（手工优先，仅提示差异）===')
n = 0
for k, v in gen.items():
    if k in man and man[k] != v:
        print(f'  {k}: 生成={v}  手工={man[k]}')
        n += 1
print(f'  差异 {n} 条')

print('\n=== B. 基名不一致（形态译名不含基名）===')
bad = 0
for k, v in man.items():
    for b, bz in base.items():
        if not isinstance(b, str) or not isinstance(bz, str):
            continue
        if b in k and k != b and bz not in v and len(b) >= 3:
            print(f'  {k} -> {v}  （基名 {b} -> {bz}）')
            bad += 1
            break
print(f'  冲突 {bad} 条')

if '--render' in sys.argv:
    print('\n=== C. 渲染产物里的半截名（假名+中文混排）===')
    dist = ROOT / 'site' / '.vitepress' / 'dist' / 'zh'
    pat = re.compile(r'[\u30a1-\u30f6]{1,}[\u4e00-\u9fff]|[\u4e00-\u9fff][\u30a1-\u30f6]{1,}')
    cnt = {}
    for f in dist.rglob('characters/*.html'):
        t = re.sub(r'<[^>]+>', '', f.read_text(encoding='utf-8', errors='ignore'))
        for m in pat.findall(t):
            cnt[m] = cnt.get(m, 0) + 1
    for w, c in sorted(cnt.items(), key=lambda kv: -kv[1])[:15]:
        print(f'  {c}\t{w}')
    print(f'  唯一组合 {len(cnt)}')
