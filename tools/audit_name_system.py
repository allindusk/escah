# -*- coding: utf-8 -*-
"""名字体系审计：词表结构 / 生成器边界 / 引擎副作用 / 性能。

只读。用法：python tools/audit_name_system.py
注意：characters.yaml 是多段文件（base/prefix/suffix/alias），同名 key 出现在不同段是合法的，
      因此重复 key 检测按「段」进行，不做全文件扫描。
"""
import json, re, sys, time, collections, yaml
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
issues = []


def load(f, sec=None):
    d = yaml.safe_load((ROOT / f).read_text(encoding='utf-8')) or {}
    if sec:
        d = d.get(sec) or {}
    return d


def dup_keys_by_section(path):
    """按 YAML 段检测重复 key（顶层缩进组之间互不干扰）。"""
    cur, seen, dup = None, collections.defaultdict(collections.Counter), {}
    for line in (ROOT / path).read_text(encoding='utf-8').split('\n'):
        if line and not line.startswith(' ') and line.rstrip().endswith(':'):
            cur = line.strip().rstrip(':')
            continue
        m = re.match(r'^  "?([^\s":]+)"?:', line)
        if m and cur:
            seen[cur][m.group(1)] += 1
    for sec, c in seen.items():
        d = {k: v for k, v in c.items() if v > 1}
        if d:
            dup[sec] = d
    return dup


print('=== 1. 词表结构 ===')
cfg = load('glossary/characters.yaml')
for sec in ('base', 'prefix', 'suffix', 'alias'):
    d = cfg.get(sec) or {}
    bad = [k for k in d if not isinstance(k, str) or not k.strip()]
    print(f'  {sec}: {len(d)} 条' + (f'  ⚠ 非法 key {bad[:3]}' if bad else ''))
    if bad:
        issues.append(f'characters.yaml {sec} 有非法 key')
dup = dup_keys_by_section('glossary/characters.yaml')
if dup:
    print(f'  ⚠ characters.yaml 段内重复 key：{dup}')
    issues.append('characters.yaml 段内重复')
else:
    print('  ✓ characters.yaml 无段内重复')
for f in ('glossary/high_freq.yaml', 'glossary/terms.yaml', 'glossary/names.yaml'):
    d = dup_keys_by_section(f)
    if d:
        print(f'  ⚠ {f} 重复 key：{ {k: len(v) for k, v in d.items()} }')
        issues.append(f'{f} 重复 key')

print('\n=== 2. 生成器边界 ===')
gen = (load('glossary/characters_generated.yaml') or {}).get('names') or {}
man = (load('glossary/names.yaml') or {}).get('names') or {}
print(f'  生成表 {len(gen)} / 手工表 {len(man)}')
empty = [k for k, v in gen.items() if not v or not str(v).strip()]
if empty:
    print(f'  ⚠ 空译名 {len(empty)}：{empty[:5]}')
    issues.append('生成表有空译名')
else:
    print('  ✓ 无空译名')
kana = [k for k, v in gen.items() if re.search(r'[\u30a1-\u30f6]', str(v))]
if kana:
    print(f'  ⚠ 译名含假名 {len(kana)}：{kana[:5]}')
    issues.append('生成表译名含假名')
else:
    print('  ✓ 生成表译名无假名残留')
diff = [(k, gen[k], man[k]) for k in gen if k in man and gen[k] != man[k]]
print(f'  生成表 vs 手工表差异 {len(diff)}' + (f'：{diff[:3]}' if diff else ' ✓'))

print('\n=== 3. 引擎副作用 ===')
sys.path.insert(0, str(ROOT / 'pipeline'))
from escah_pipeline import i18n as I  # noqa: E402
t0 = time.time()
I.render_locale('characters/エスカレイヤー', 'zh')
print(f'  首次渲染（含词表加载）{(time.time() - t0) * 1000:.0f} ms')
print(f'  _HF_SUB_MAP {len(I._HF_SUB_MAP or {})} / _NAME_MAP {len(I._NAME_MAP or {})}')
short = [k for k in (I._HF_SUB_MAP or {}) if len(k) < 3 and re.search(r'[\u30a1-\u30f6]', k)]
if short:
    print(f'  ⚠ 子串层仍含 2 字假名条目 {len(short)}：{short[:5]}')
    issues.append('子串层仍有短假名条目')
else:
    print('  ✓ 子串层已排除 2 字假名条目（避免劈开长专名）')

print('\n=== 4. 性能 ===')
t0 = time.time()
for _ in range(20):
    I.render_locale('characters/エスカレイヤー', 'zh')
cost = (time.time() - t0) / 20
print(f'  {cost * 1000:.1f} ms/页，450 页约 {cost * 450:.1f} s')

print('\n=== 5. 结论 ===')
if issues:
    for i in issues:
        print('  ⚠', i)
else:
    print('  ✓ 无阻断性问题')
