# -*- coding: utf-8 -*-
"""角色名生成器：由「形态基名表 + 形态词素表」自动拼出全站角色中文名。

输入  glossary/characters.yaml        （base / prefix / suffix / alias）
      data/parsed/characters/*.json   （name）
输出  glossary/characters_generated.yaml  -> names: {日文名: 中文名}
      tools/_char_name_report.txt         -> 一致性冲突 / 未覆盖报告

拆解：name = 最长前缀 + 基名 + 最长后缀
规则  1. alias 命中 → 直接用
      2. name 本身就是 base → 用 base 译名
      3. 拆出 (prefix, base, suffix) 且 base 在表中 → 组合
      4. 拼不出来 → 退回角色 JSON 的 name_zh（若有），记入报告
校验  同一基名的所有形态，中文名必须包含该基名的中文译法。
"""
import json, sys, yaml
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
CHAR = ROOT / 'data' / 'parsed' / 'characters'
CFG = yaml.safe_load((ROOT / 'glossary' / 'characters.yaml').read_text(encoding='utf-8')) or {}
BASE = CFG.get('base') or {}
PRE = {k: v for k, v in (CFG.get('prefix') or {}).items() if len(k) <= 8}
SUF = CFG.get('suffix') or {}
ALIAS = CFG.get('alias') or {}
PRE_SORTED = sorted(PRE, key=len, reverse=True)
SUF_SORTED = sorted(SUF, key=len, reverse=True)

out, rows, missing = {}, [], []
for p in sorted(CHAR.glob('*.json')):
    d = json.load(open(p, encoding='utf-8'))
    ja = d.get('name') or p.stem
    cur = d.get('name_zh') or ''
    if ja in ALIAS:
        out[ja] = ALIAS[ja]
        rows.append((ja, '', ALIAS[ja], 'alias'))
        continue
    if ja in BASE:
        out[ja] = BASE[ja]
        rows.append((ja, ja, BASE[ja], 'base'))
        continue
    rest, pre_zh, suf_zh = ja, '', ''
    for x in PRE_SORTED:
        if ja.startswith(x) and len(ja) > len(x):
            pre_zh, rest = PRE[x], ja[len(x):]
            break
    for x in SUF_SORTED:
        if rest.endswith(x) and len(rest) > len(x):
            suf_zh, rest = SUF[x], rest[:len(rest) - len(x)]
            break
    if rest in BASE:
        out[ja] = pre_zh + BASE[rest] + suf_zh
        rows.append((ja, rest, out[ja], 'compose'))
    else:
        if cur:
            out[ja] = cur
        missing.append((ja, rest, cur))
        rows.append((ja, rest, cur, 'fallback'))

# 一致性校验：按基名分组
groups = {}
for ja, base, zh, how in rows:
    if base:
        groups.setdefault(base, []).append((ja, zh))
conf = []
for base, forms in groups.items():
    bz = BASE.get(base) or ''
    if not bz:
        continue
    for f, z in forms:
        if z and bz not in z:
            conf.append((base, bz, f, z))

rep = [f'角色 {len(out)} / 基名 {len(groups)}',
       f'\n=== 一致性冲突 {len(conf)} ===']
for base, bz, f, z in conf:
    rep.append(f'基名 {base}={bz}\t{f} -> {z}')
rep.append(f'\n=== 未拆解（用现有 name_zh 兜底）{len(missing)} ===')
for ja, rest, cur in missing:
    rep.append(f'{ja}\trest={rest}\tzh={cur or "-"}')
(ROOT / 'tools' / '_char_name_report.txt').write_text('\n'.join(rep), encoding='utf-8')

(ROOT / 'glossary' / 'characters_generated.yaml').write_text(
    '# 自动生成，请勿手改。改 glossary/characters.yaml 后重跑 tools/gen_char_names.py\n'
    + yaml.safe_dump({'names': out}, allow_unicode=True, sort_keys=True, width=200),
    encoding='utf-8')
print('\n'.join(rep[:45]))
print(f'\n已写 glossary/characters_generated.yaml（{len(out)} 条）')
