"""信号抽取：把 char_data.json 压成可比较的紧凑信号，供大模型独立推理用。

不依赖任何攻略页/官方推荐榜，只看角色自身数据：
- 稀有度、阵营、攻击类型、获取方式
- lv100 五维（体力/攻/防/魔/魔抗）
- 必杀技、固有效果文本 → 机制标签分类

输出到 stdout（由调用方重定向到 _signals.txt 阅读）。
"""
import json, re, sys, io
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = 'llm_reco/char_data.json'
data = json.load(open(P, encoding='utf-8'))

# ---- 机制关键词（日+中，覆盖 uniques/ultimates 文本）----
# 每条 = (标签, [ja 关键词..., zh 关键词...])
TAGS = [
    ('不撤退',      ['撤退しない', '撤退しなく', '退場しない', '撤退しなくなる', '不会撤退']),
    ('体力维持',    ['スタミナ', '体力', 'ST', '持続', '減少を防', '減少を抑', '低下を防']),
    ('全异常免疫',  ['全ての異常', 'すべての異常', '全异常免疫', 'あらゆる異常', '全部异常']),
    ('魅惑免疫',    ['魅惑', '魅了']),
    ('束缚免疫',    ['束縛', '呪縛']),
    ('眩晕免疫',    ['眩晕', '晕眩']),
    ('异常解除',    ['異常を回復', '異常を治', '異常状態を回復', '解除', '異常を取り除']),
    ('速度辅助',    ['行動速度', 'スピード', '速度', '行動間隔', 'クイック']),
    ('充能辅助',    ['必殺ゲージ', '必殺技ゲージ', 'ゲージ', 'チャージ', '充能', '必杀槽', '必殺技の溜', '必殺技を溜']),
    ('攻击buff',    ['攻撃力', '攻撃上昇', '攻撃力アップ', '与えるダメージ', '攻撃力を上', '伤害上升', '攻击力上升']),
    ('魔法buff',    ['魔法力', '魔法上昇', '魔法力アップ', '魔法力を上', '魔法力上升']),
    ('防御buff',    ['防御力', '防御上昇', '防御力アップ', '防御力を上', '防御力上升']),
    ('伤害减buff',  ['受けるダメージ', 'ダメージを軽減', '被ダメージ', '伤害减轻', '受到伤害', 'ダメージカット', ' damage cut']),
    ('防御debuff',  ['防御力ダウン', '防御力を下', '防御力下降', '防御力を減', '防御力を引']),
    ('魔抗debuff',  ['魔法抵抗力ダウン', '魔法抵抗力を下', '魔法抵抗下降', '魔法抵抗を下']),
    ('治疗',        ['体力を回復', '回復', '回復する', '治癒', '回復させ', '体力回復', '回复']),
    ('即死',        ['即死', '瞬殺']),
    ('防御无视',    ['防御無視', '防御を無視', '防御力を無視', '防御无视']),
    ('暴击',        ['クリティカル', '暴击', '会心']),
    ('连击',        ['連撃', 'コンボ', '连击']),
    ('AoE全体',     ['全体', '全員', '全ての敵', '范围内', '範囲']),
    ('贯通/破防',   ['貫通', '贯通', 'ブレイク', 'break', 'Break']),
    ('复活',        ['蘇生', '復活', '生き返', '复活']),
    ('吸血',        ['吸収', '吸血']),
    ('分身/召唤',   ['分身', '召喚', 'シンクロ', '召唤']),
    ('必定hit',     ['必中', '命中率', '回避無視', '回避を無視']),
    ('属性特攻',    ['太陽', '月', '星', '太阳', '月球', '星星']),
]

def text_of(rec):
    parts = []
    for u in rec.get('uniques', []):
        parts.append(u.get('eff_ja', '') + ' ' + u.get('eff_zh', ''))
    for u in rec.get('ultimates', []):
        parts.append(u.get('eff_ja', '') + ' ' + u.get('eff_zh', ''))
    return ' '.join(parts)

def tag_rec(rec):
    t = text_of(rec)
    tags = []
    for label, kws in TAGS:
        for kw in kws:
            if kw.lower() in t.lower():
                tags.append(label)
                break
    return tags

def short_obtain(s):
    s = (s or '').strip()
    if not s:
        return '?'
    for k, v in [('交換所', '交换所'), ('ガチャ', '卡池'), ('ストーリー', '剧情'), ('配布', '赠送'),
                 ('イベント', '活动'), ('限定', '限定'), ('常設', '常驻'), ('ミッション', '任务')]:
        if k in s:
            return v
    return s[:8]

# ---- 1) 紧凑总表 ----
print('=' * 120)
print('【总表】角色 | 稀有 | 阵营 | 攻型 | 体/攻/防/魔/魔抗 | 获取 | 机制标签')
print('=' * 120)
rows = []
for rec in data:
    st = rec.get('stats_lv100') or {}
    sta = st.get('スタミナ'); atk = st.get('攻撃力'); dfn = st.get('防御力')
    mag = st.get('魔法力'); mres = st.get('魔法抵抗力')
    tags = tag_rec(rec)
    rows.append((rec, sta, atk, dfn, mag, mres, tags))
    line = ' | '.join([
        rec.get('name', ''),
        str(rec.get('rarity', '?')),
        (rec.get('faction', '') or '?')[:6],
        (rec.get('atk_type', '') or '?')[:4],
        '/'.join('-' if v is None else str(v) for v in [sta, atk, dfn, mag, mres]),
        short_obtain(rec.get('obtain')),
        ','.join(tags) if tags else '-',
    ])
    print(line)

# ---- 2) 五维榜 ----
def leaderboard(key, topn=20):
    vals = [(rec.get('name'), (rec.get('stats_lv100') or {}).get(key)) for rec in data]
    vals = [(n, v) for n, v in vals if isinstance(v, int)]
    vals.sort(key=lambda x: -x[1])
    return vals[:topn]

print()
print('=' * 60)
print('【五维榜 top20】')
print('=' * 60)
for key in ['スタミナ', '攻撃力', '防御力', '魔法力', '魔法抵抗力']:
    print(f'\n--- {key} ---')
    for n, v in leaderboard(key):
        print(f'  {v:>6}  {n}')

# ---- 3) 机制分组（仅列名字）----
print()
print('=' * 60)
print('【机制分组】')
print('=' * 60)
group = defaultdict(list)
for rec, sta, atk, dfn, mag, mres, tags in rows:
    for t in tags:
        group[t].append((rec.get('rarity'), rec.get('name')))
for label, kws in TAGS:
    members = group.get(label, [])
    if not members:
        continue
    members.sort(key=lambda x: (str(x[0])))
    print(f'\n[{label}] ({len(members)})')
    print('  ' + ', '.join(f'{n}({r})' for r, n in members))

# ---- 4) 稀有度 × 获取 分布 ----
print()
print('=' * 60)
print('【稀有度×获取 分布】')
print('=' * 60)
rc = Counter((str(r.get('rarity')), short_obtain(r.get('obtain'))) for r in data)
for (rar, ob) in sorted(rc):
    print(f'  {rar:>4} {ob:<6} {rc[(rar, ob)]:>3}')
print('\n总角色数:', len(data))
print('稀有度:', dict(Counter(str(r.get('rarity')) for r in data)))
