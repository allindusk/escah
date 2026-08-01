# -*- coding: utf-8 -*-
"""v0.6 Step1-2：角色分类（输出/辅助/生存），输出内再分（単体/全体/連撃）。

来源：llm_reco/char_data.json（extract_chars.py 抽取，含 combat：连击率/行动速度/必杀充能）。
分类依据（均来自游戏机制原文 battle.md / raid-buff-debuff.md）：
  · 输出：拥有伤害型必杀（敵〇〇N倍 倍率>0）。
  · 辅助：以 buff/debuff/充能/速度/治疗 为主要职责、自身直伤必杀弱或无。
  · 生存：治疗/免疫/不撤退/复活/减伤 为主要职责。
  · 输出子类：敵単体→単体；敵横一列→横列；敵全体→全体；连击率≥阈值→連撃（必杀倍率权重下调）。
"""
import json, re, io, sys
from collections import defaultdict, Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DATA = json.load(open('llm_reco/char_data.json', encoding='utf-8'))
BY = {r['name']: r for r in DATA}

# ---------- 文本解析（与 _char_score.py 同源） ----------
def norm(t):
    return (t or '').replace('％', '%')

def _near(text, pos, win=44):
    return text[pos:pos+win]

DOWN_VERB = r'(?:ダウン|を下|下降|低下|減少|降低|下げ|下)'
UP_VERB = r'(?:アップ|上昇|上がる|上升|提升|増)'

def _kit_text(rec):
    parts = []
    for u in (rec.get('ultimates') or []):
        parts.append(u.get('eff_ja', '') + ' ' + u.get('eff_zh', ''))
    for u in (rec.get('uniques') or []):
        parts.append(u.get('eff_ja', '') + ' ' + u.get('eff_zh', ''))
    return ' '.join(parts)

def parse_ult(text):
    t = norm(text); mult = 0; aoe = False; tgt = ''
    for m in re.finditer(r'敵(単体|横一列|全体).{0,30}?(\d+)倍', t):
        v = int(m.group(2)); mult = max(mult, v)
        if m.group(1) == '全体':
            aoe = True
        tgt = m.group(1)
    for m in re.finditer(r'必殺威力×(\d+)', t):
        mult = max(mult, int(m.group(1)))
    return mult, aoe, tgt

def parse_def_down(text):
    t = norm(text); best = 0.0
    for kw in ('防御', '攻防', '防速'):
        for m in re.finditer(kw + r'.{0,16}?(\d+)%', t):
            if re.search(DOWN_VERB, t[m.start():m.start()+44]):
                best = max(best, int(m.group(1)))
    return min(1.0, best/100.0)

def parse_atk_buff(text):
    t = norm(text); best = 0.0
    for m in re.finditer(r'攻撃力?.{0,12}?(\d+)%', t):
        if re.search(UP_VERB, t[m.start():m.start()+44]):
            best = max(best, int(m.group(1)))
    return best/100.0

def parse_dmg_up(text):
    t = norm(text); best = 0.0
    for m in re.finditer(r'与.{0,10}?ダメ.{0,14}?(\d+)%', t):
        if re.search(UP_VERB, t[m.start():m.start()+44]):
            best = max(best, int(m.group(1)))
    for m in re.finditer(r'ダメージ.{0,8}?(\d+)%', t):
        if re.search(UP_VERB, t[m.start():m.start()+44]):
            best = max(best, int(m.group(1)))
    return best/100.0

def parse_speed(text):
    t = norm(text); best = 0.0
    for m in re.finditer(r'速度.{0,10}?(\d+)%', t):
        if re.search(UP_VERB, t[m.start():m.start()+44]):
            best = max(best, int(m.group(1)))
    return best/100.0

def parse_charge(text):
    t = norm(text); best = 0.0
    for m in re.finditer(r'必殺.{0,6}?(?:ゲージ|値).{0,6}?(\d+)%', t):
        best = max(best, int(m.group(1)))
    for m in re.finditer(r'チャージ.{0,6}?(\d+)%', t):
        best = max(best, int(m.group(1)))
    for m in re.finditer(r'充能.{0,6}?(\d+)%', t):
        best = max(best, int(m.group(1)))
    return best/100.0

def parse_guard(text):
    t = norm(text); best = 0.0
    for m in re.finditer(r'防御.{0,10}?(\d+)%', t):
        if re.search(UP_VERB, _near(t, m.start())):
            best = max(best, int(m.group(1)))
    for m in re.finditer(r'与.{0,10}?ダメ.{0,14}?(\d+)%', t):
        if re.search(DOWN_VERB, _near(t, m.start())):
            best = max(best, int(m.group(1)))
    return min(1.0, best / 100.0)

def has(text, *pats):
    t = norm(text)
    return any(re.search(p, t, re.IGNORECASE) for p in pats)

HEAL = (r'回復', r'回复', r'治癒', r'回血')
IMMUNE = (r'無効', r'免疫', r'不受影响')
NO_RETREAT = (r'撤退しない', r'撤退しなく', r'不会撤退')
REVIVE = (r'蘇生', r'復活', r'生き返', r'复活')
HARDCC = (r'スタン', r'魅了', r'呪縛', r'束縛', r'眩晕', r'魅惑', r'束缚')
DEC_CC = (r'異常を回復', r'異常状態を回復', r'異常を治', r'異常を取り除', r'解除', r'净化')

# ---------- 连击阈值（Step3 用户确认：60%；基础连击率上限70%） ----------
COMBO_THRESHOLD = 60.0   # 连击率≥60% 视为"连击输出型"（仅 3 人：バビロニア・ニル/体育祭のキリエル/正月の切裂余命）

# ---------- 逐角色分类 ----------
def classify(rec):
    text = _kit_text(rec)
    ult_mult, aoe, tgt = parse_ult(text)
    cb = rec.get('combat') or {}
    combo_rate = cb.get('combo_rate')
    has_dmg_ult = ult_mult > 0
    flags = {
        'atk_buff': parse_atk_buff(text) > 0,
        'def_down': parse_def_down(text) > 0,
        'dmg_up': parse_dmg_up(text) > 0,
        'speed': parse_speed(text) > 0,
        'charge': parse_charge(text) > 0,
        'heal': has(text, *HEAL),
        'immune': has(text, *IMMUNE),
        'no_retreat': has(text, *NO_RETREAT),
        'revive': has(text, *REVIVE),
        'hardcc': has(text, *HARDCC),
        'dec_cc': has(text, *DEC_CC),
        'guard': parse_guard(text) > 0,
    }
    supportish = flags['atk_buff'] or flags['def_down'] or flags['speed'] or flags['charge']
    survivalish = flags['heal'] or flags['immune'] or flags['no_retreat'] or flags['revive'] or flags['guard']
    # 主职：拥有伤害型必杀才算"输出"；否则按生存/辅助/其他判定
    if has_dmg_ult:
        primary = '输出'
    elif survivalish:
        primary = '生存'
    elif supportish:
        primary = '辅助'
    else:
        primary = '其他'
    # 输出子类
    sub = ''
    if primary == '输出':
        if combo_rate is not None and combo_rate >= COMBO_THRESHOLD:
            sub = '連撃'
        elif tgt == '単体':
            sub = '単体'
        elif tgt == '横一列':
            sub = '横列'
        elif tgt == '全体':
            sub = '全体'
        else:
            sub = '其他'
    return {
        'name': rec['name'], 'rarity': str(rec.get('rarity')), 'primary': primary,
        'sub': sub, 'ult_mult': ult_mult, 'aoe': aoe, 'tgt': tgt,
        'combo_rate': combo_rate, 'has_dmg_ult': has_dmg_ult, 'flags': flags,
    }

CLS = {n: classify(r) for n, r in BY.items()}

# ---------- 统计 ----------
print('=' * 100)
print(f'v0.6 Step1-2 角色分类（共 {len(DATA)} 人）  连击阈值={COMBO_THRESHOLD}%')
print('=' * 100)

prim = Counter(c['primary'] for c in CLS.values())
print('\n【主职分布】')
for k in ['输出', '辅助', '生存']:
    print(f'  {k}: {prim[k]:>3}')

print('\n【输出子类分布（输出 {0} 人内）】'.format(prim['输出']))
subc = Counter(c['sub'] for c in CLS.values() if c['primary'] == '输出')
for k in ['単体', '横列', '全体', '連撃', '其他']:
    print(f'  {k}: {subc[k]:>3}')

# 连击率分布（辅助选阈值）
cr_all = [c['combo_rate'] for c in CLS.values() if c['combo_rate'] is not None]
buckets = defaultdict(int)
for v in cr_all:
    buckets[int(v // 10) * 10] += 1
print('\n【连击率分布（每10%一档）】')
for b in sorted(buckets):
    print(f'  {b:>3}–{b+9:<3}: {buckets[b]:>3}  ' + '#' * buckets[b])

# 输出 TOP 连击率（检视连击型是否真的是输出主力）
print('\n【连击率最高的输出角色 TOP20】')
out_combo = sorted([c for c in CLS.values() if c['primary'] == '输出' and c['combo_rate']],
                   key=lambda c: -(c['combo_rate'] or 0))[:20]
for c in out_combo:
    print(f"  {c['name']:<26} {c['rarity']:<4} 连击率{c['combo_rate']:>5.0f}%  必杀×{c['ult_mult']}  [{c['sub']}]")

# 输出内各子类代表
print('\n【输出各子类代表（按必杀倍率/连击率）】')
for sub in ['単体', '横列', '全体', '連撃']:
    members = [c for c in CLS.values() if c['primary'] == '输出' and c['sub'] == sub]
    ex = sorted(members, key=lambda c: -(c['ult_mult'] or 0))[:6]
    print(f"  [{sub}] 共{len(members)}: " + '、'.join(f"{m['name']}(×{m['ult_mult']})" for m in ex))

# 非输出角色（无伤害必杀）按主职分布，便于核对生存/辅助落点
non_out = [c for c in CLS.values() if c['primary'] != '输出']
print('\n【非输出角色主职分布】 ' + ' / '.join(f"{k}:{sum(1 for c in non_out if c['primary']==k)}" for k in ['辅助','生存','其他']))
hi_combo_nonout = [c for c in non_out if c['combo_rate'] and c['combo_rate'] >= COMBO_THRESHOLD]
if hi_combo_nonout:
    print('  （其中连击率≥阈值但无伤害必杀，属纯连击辅助/生存，已不计入連撃输出）:')
    for c in hi_combo_nonout[:12]:
        print(f"    {c['name']:<24} {c['rarity']:<4} {c['primary']} 连击率{c['combo_rate']:.0f}%")

# 写出分类 JSON（供 _char_score.py / 后续复用）
out = {
    'combo_threshold': COMBO_THRESHOLD,
    'chars': [
        {'name': c['name'], 'rarity': c['rarity'], 'primary': c['primary'], 'sub': c['sub'],
         'ult_mult': c['ult_mult'], 'aoe': c['aoe'], 'tgt': c['tgt'],
         'combo_rate': c['combo_rate'], 'flags': c['flags']}
        for c in CLS.values()
    ],
}
json.dump(out, open('llm_reco/classification.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n已写出 llm_reco/classification.json')
