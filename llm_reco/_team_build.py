"""团队构建分析：从 370 角色中按"队伍职能"打标签，统计稀缺度，找出高密度多职角色，
并用贪心覆盖算法拼出 5 人均衡队（输出+生存+增益齐全）。

不依赖任何攻略页/官方推荐榜，只基于 char_data.json 自身文本与五维。
输出到 stdout（调用方重定向到 _team_build.txt 阅读）。
"""
import json, re, sys, io
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = 'llm_reco/char_data.json'
data = json.load(open(P, encoding='utf-8'))

# ---- 队伍职能标签： (职能, 正则) ----
# 注意真实文本写法：防御20%ダウン / 攻防60%ダウン / 攻撃力50％アップ（数字夹在中间）
ROLE_RE = {
    '降防':   r'防御.{0,6}(ダウン|を下|を減|下降|低下|減少)|攻防.{0,6}(ダウン|を下)|防速.{0,6}ダウン|降低防御|降低敌方防御|敵の防御',
    '攻buff': r'攻撃力?.{0,8}(アップ|上昇|上がる|を上|上升|提升)|攻击力提升|攻击力上升',
    '增伤':   r'与ダメ.{0,6}アップ|与えるダメージ.{0,6}(アップ|上昇)|伤害提升|增伤|ダメージ上昇',
    '速度':   r'行動速度|スピード|速度|行動間隔|クイック|素早さ|攻击速度|行動を早',
    '充能':   r'必殺ゲージ|必殺技ゲージ|必殺値|チャージ|充能|必殺技の溜|必殺技を溜|ゲージを上|必杀槽',
    '治疗':   r'体力を回復|回復|回復する|治癒|回復させ|体力回復|回复|回血',
    '减伤':   r'受けるダメージ|ダメージを軽減|被ダメージ|ダメージカット|ダメージ軽減|受到伤害|伤害减轻|伤害减少|防御.{0,6}(アップ|上昇)|与ダメ.{0,6}ダウン|攻防.{0,6}ダウン',
    '免疫':   r'全ての異常|すべての異常|全异常|あらゆる異常|免疫|無効|不受影响',
    '解控':   r'異常を回復|異常状態を回復|異常を治|異常を取り除|状態異常を回復|解除|净化',
    '不撤退': r'撤退しない|撤退しなく|退場しない|撤退しなくなる|不会撤退',
    '复活':   r'蘇生|復活|生き返|复活|蘇',
    '硬控':   r'スタン|眩晕|晕眩|魅了|魅惑|呪縛|束縛|束缚',
}
ROLE_KEYS = list(ROLE_RE.keys())

def text_of(rec):
    parts = []
    for u in rec.get('uniques', []) or []:
        parts.append((u.get('eff_ja', '') + ' ' + u.get('eff_zh', '')))
    for u in rec.get('ultimates', []) or []:
        parts.append((u.get('eff_ja', '') + ' ' + u.get('eff_zh', '')))
    return ' '.join(parts)

_COMPILED = {k: re.compile(v, re.IGNORECASE) for k, v in ROLE_RE.items()}

def role_of(rec):
    t = text_of(rec)
    roles = set()
    for label, rx in _COMPILED.items():
        if rx.search(t):
            roles.add(label)
    # 输出代理：高数值（atk/mag 进前段）或 高倍率必杀（×>=3）或 连击
    st = rec.get('stats_lv100') or {}
    atk = st.get('攻撃力') or 0
    mag = st.get('魔法力') or 0
    high = (atk >= 450 or mag >= 450)
    mult = re.search(r'×(\d+)', t)
    big_mult = mult and int(mult.group(1)) >= 3
    if high or big_mult or ('連撃' in t) or ('回攻' in t):
        roles.add('输出')
    return roles

# ---- 计算每个角色的职能 ----
info = {}
for rec in data:
    info[rec['name']] = {
        'rec': rec,
        'rarity': str(rec.get('rarity')),
        'roles': role_of(rec),
        'atk': (rec.get('stats_lv100') or {}).get('攻撃力') or 0,
        'mag': (rec.get('stats_lv100') or {}).get('魔法力') or 0,
        'sta': (rec.get('stats_lv100') or {}).get('スタミナ') or 0,
        'faction': rec.get('faction', ''),
        'atk_type': rec.get('atk_type', ''),
    }

# ---- 1) 各职能稀缺度（按稀有度计数）----
print('=' * 100)
print('【职能稀缺度】持有该职能的角色数（按稀有度）；数字越小越珍贵')
print('=' * 100)
for role in ROLE_KEYS:
    holders = [n for n, v in info.items() if role in v['roles']]
    by_rar = Counter(info[n]['rarity'] for n in holders)
    print(f'  {role:<6} 总{len(holders):>3}  [SSR {by_rar.get("SSR",0):>3} / SR {by_rar.get("SR",0):>3} / R {by_rar.get("R",0):>3}]')

# ---- 2) 高密度多职角色（覆盖 >=3 职能）----
print()
print('=' * 100)
print('【高密度多职角色】覆盖职能数 >= 3（5 框塞满的关键：一人顶多人）')
print('=' * 100)
multi = [(n, v) for n, v in info.items() if len(v['roles']) >= 3]
multi.sort(key=lambda x: (-len(x[1]['roles']), x[1]['rarity']))
for n, v in multi:
    print(f"  [{len(v['roles'])}职/{v['rarity']}] {n}  -> {','.join(sorted(v['roles']))}")

# ---- 3) 关键职能的稀有持有者速览 ----
print()
print('=' * 100)
print('【关键职能持有者（稀缺职能重点列）】')
print('=' * 100)
for role in ['降防', '充能', '速度', '免疫', '不撤退', '复活', '解控', '减伤']:
    holders = [n for n, v in info.items() if role in v['roles']]
    # 优先显示 SSR/SR
    holders.sort(key=lambda n: (info[n]['rarity'] != 'SSR', info[n]['rarity'] != 'SR', n))
    sample = holders[:14]
    print(f'\n[{role}] ({len(holders)}人) 例: ' + '、'.join(f'{n}({info[n]["rarity"]})' for n in sample))

# ---- 4) 贪心覆盖：拼 5 人均衡队 ----
# 强制职能（raid 均衡队最小集）：输出 + 降防 + 速度 + 充能 + 治疗(生存)
MAND = ['输出', '降防', '速度', '充能', '治疗']
# 生存完整化：治疗 位最好同时带 免疫/减伤/不撤退 之一
SURV_EXTRA = ['免疫', '减伤', '不撤退', '复活']

def team_score(team):
    """team: list of names. 返回 (覆盖强制职能数, 覆盖总职能数, 稀有职能加权)"""
    union = set()
    for n in team:
        union |= info[n]['roles']
    mand_hit = sum(1 for r in MAND if r in union)
    # 生存完整：治疗 且 至少一项 surv_extra
    surv_ok = ('治疗' in union) and any(r in union for r in SURV_EXTRA)
    rare = {'降防':5, '充能':4, '速度':4, '免疫':6, '不撤退':7, '复活':8, '解控':3, '减伤':3, '硬控':2}
    rare_w = sum(rare.get(r, 0) for r in union)
    return (mand_hit, 1 if surv_ok else 0, len(union), rare_w)

def greedy_team(pool=None, prefer_rar=None, must_cover=None):
    """贪心：先补强制职能缺口，再用剩余槽位最大化总覆盖+生存完整。
    pool: 限定候选（如只 R/SR）。prefer_rar: 排序偏好。must_cover: 额外必须职能。"""
    must = list(MAND) + (must_cover or [])
    cand = list(info.keys()) if pool is None else pool
    team = []
    covered = set()
    # 阶段A：每轮选能新增最多"必须职能"的候选；并列时选总职能多、且稀有度符合偏好
    def sort_key(n):
        v = info[n]
        rar_rank = {'SSR':0, 'SR':1, 'R':2}.get(v['rarity'], 3)
        if prefer_rar == 'low':   # 新手：偏好 R/SR
            rar_rank = {'R':0, 'SR':1, 'SSR':2}.get(v['rarity'], 3)
        return (-len(v['roles'] - covered), -len(v['roles']), rar_rank, n)
    # 迭代式补 must 缺口
    progress = True
    while progress and len(team) < 5:
        progress = False
        cand_sorted = sorted(cand, key=sort_key)
        for n in cand_sorted:
            if n in team:
                continue
            new_must = [r for r in must if r in info[n]['roles'] and r not in covered]
            if new_must:
                team.append(n)
                covered |= info[n]['roles']
                progress = True
                break
    # 阶段B：剩余槽位最大化总覆盖 + 优先补 surv_extra / 硬控
    extra_pref = ['免疫', '不撤退', '复活', '减伤', '解控', '硬控', '攻buff']
    while len(team) < 5:
        best = None; best_key = None
        for n in cand:
            if n in team:
                continue
            add = info[n]['roles'] - covered
            # 优先稀有职能 + 生存额外 + 总覆盖
            rare = {'降防':5,'充能':4,'速度':4,'免疫':6,'不撤退':7,'复活':8,'解控':3,'减伤':3,'硬控':2,'攻buff':1}
            val = sum(rare.get(r, 0) for r in add) + 0.5*len(add)
            key = (-val, n)
            if best_key is None or key < best_key:
                best_key = key; best = n
        if best is None:
            break
        team.append(best); covered |= info[best]['roles']
    return team

def show_team(title, team):
    print(f'\n--- {title} ---')
    for i, n in enumerate(team, 1):
        v = info[n]
        print(f'  {i}. {n} [{v["rarity"]}]  职能={",".join(sorted(v["roles"]))}')
    sc = team_score(team)
    print(f'  >> 强制职能覆盖 {sc[0]}/5, 生存完整 {"是" if sc[1] else "否"}, 总覆盖职能 {sc[2]}, 稀有权重 {sc[3]}')

print()
print('=' * 100)
print('【5 人均衡队（贪心覆盖）】')
print('=' * 100)
show_team('A. 顶配均衡队（不限稀有度）', greedy_team())
show_team('B. 新手友好队（仅 R/SR）', greedy_team(
    pool=[n for n in info if info[n]['rarity'] in ('R', 'SR')], prefer_rar='low'))
show_team('C. 高难 raid 居座队（强制含 不撤退/体力维持）', greedy_team(
    must_cover=['不撤退']))
show_team('D. 暴力输出队（强制含 2 输出 + 降防 + 充能 + 治疗）', greedy_team(
    must_cover=['输出']))

print('\n总角色数:', len(data))
