# -*- coding: utf-8 -*-
"""v0.8 单角色固定强度量化模型（raid 专用 · 通用可复用 · 真实频率公式 · 真实觉醒表 · 真实两件配装）

==================== 场景固定设定（用户指定，建通用模型的前提） ====================
终局副本有 4 种：raid / B宇宙 / 广域战 / 全域战。本模型**只攻破 raid**；
B宇宙/广域战/全域战 暂时仅占位（见文末）。

为建立"通用模型"，把除「角色 kit + 真实战斗细节」以外的一切**全部固定为常数**：
  【BOSS 固定】
    · 机制常亮：BOSS 所有机制始终生效
    · 固定伤害：BOSS 对我方造成的伤害为固定值
    · 体力固定消耗：讨伐战 スタミナ -2%/s（百分比，双防无效）
    · 固定防御：BOSS 减伤率固定为 R_ref（Step3 用户确认 = 0.50，古纳冈类）
  【角色固定】
    · 满星 + 100 级 → 直接用 stats_lv100
    · 必杀技/固有效果 = 觉醒+(+) 版本
    · 觉醒属性强化固定到强化次数上限（2026-07-30 用户给出真实觉醒表，修正 v0.6 错误常数）：
        - 行動速度：-0.1×20次 = 最多 -2 秒（扁平秒数！非百分比），强化下限 3 sec
        - 必杀充能：+0.3×20次 = 最多 +6pt，强化上限 15%（基础≥15 不再受益）
        - 攻/魔：+1%×20次 = +20%（全员同幅，只抬绝对DPS）
        - 连击率 +20(上限50%) 不采用：基础 50/70 档已达/超上限无收益；
          0 档必杀型点了反而 interval_ult×1.2 拖慢必杀（连击使行动条不前进），理性不点
    · 固定装备（2026-07-30 用户拍板，v0.8 替换 v0.7 占位配装）：**仅两件主装备**
        - 火箭引擎/咆哮猛虎（满级）：行动速度 -50%（百分比缩短）
        - 冲击腰带（满级）：攻击力&魔法力 +50%
        - **副装贴片全部删除**（多变量）；仁王纳豆也删除（与部分角色技能效果冲突，多变量）
        - 旧占位 主装+300 / 贴片B8降防30%·B1攻30%·B3速20% 全部作废
  【真实数据（来自 char_data.json.combat，extract_chars.py 抽取）】
    · 行動速度：行动间隔(秒)，3.0(最快)~10.0(最慢)
    · 必殺充填量：每次普攻增加的必杀槽(%)，3.5~20.0
    · 連撃率：普攻触发连击的概率，0~70%

→ 因此「角色强度 = 固定场景下的 kit + 真实战斗细节 函数」，新增角色补 char_data.json 即出分。

==================== 损伤频率模型（battle.md 机制，Step5 核心） ====================
普攻一次的时间（觉醒 -2 秒扁平下限3s → 火箭 -50% 百分比缩短 → 自身速度buff）：
    eff_speed  = max(行動速度(sec) - 2.0, 3.0)          # 觉醒扁平减秒，下限3sec
    interval   = eff_speed × (1 - 火箭50%) / (1 + 自身速度buff)
连击使行动计量条(☆)不前进 → 连击越多行动周期越慢（battle.md 原文）：
    interval_ult = interval × (1 + 連撃率)        # 连击率越高，必杀/普攻节奏越慢
每次普攻的必杀槽充填量（觉醒最多 +6pt，强化上限 15%）：
    charge_eff = min(max(必殺充填量, min(必殺充填量+6, 15)), 100)
    （基础<15 → +6 但封顶15；基础≥15 → 保持原值不受益）
必杀释放频率（每秒）：
    ult_casts/s = (charge_eff/100) / interval_ult
普攻频率：
    atks/s = 1 / interval_ult
连击伤害倍率（首击衰减20%→下限30%，battle.md）：
    combo_mult = 1 + Σ_{n≥1} 連撃率ⁿ × decay(n)，decay=0.8/0.6/0.4/0.3(≥4击)
普攻伤害 = 基础单击 × (暴击base + 连击追加不暴击) × combo_mult × atks/s
必杀伤害 = 基础单击 × 必杀倍率 × FEVER(3) × 击破(1.5) × ult_casts/s
  （连击不暴击 → base击部分暴击、连击追加部分不暴击；FEVER/击破仅必杀）
DPS = 普攻DPS + 必杀DPS
→ 连击型：连击率高 → interval_ult↑(必杀变慢) + combo_mult↑(普攻变多)，必杀权重自然下降。
===============================================================================
"""
import json, re, io, sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = 'llm_reco/char_data.json'
DATA = json.load(open(P, encoding='utf-8'))
BY = {r['name']: r for r in DATA}

# ---------- 固定常数（机制事实 + 用户固定场景） ----------
FEVER = 3.0
CRIT = 1.25
BREAK = 1.5
# ---- 固定装备（2026-07-30 用户拍板：仅两件主装，副装/纳豆删除避免多变量） ----
EQ_ROCKET_SPEED = 0.50 # 火箭引擎/咆哮猛虎(满级)：行动速度 -50%（interval ×0.5）
EQ_BELT_ATK = 0.50     # 冲击腰带(满级)：攻击力&魔法力 +50%（与角色攻buff加算）
# ---- 觉醒属性强化（2026-07-30 用户真实觉醒表，修正 v0.6 错误常数） ----
AWK_SPEED_SEC = 2.0    # 行动速度：-0.1×20次=最多-2秒（扁平），强化下限 3 sec
AWK_SPEED_FLOOR = 3.0  # 行动速度强化下限（sec）
AWK_CHARGE = 6.0       # 必杀充能：+0.3×20次=最多+6pt
AWK_CHARGE_CAP = 15.0  # 必杀充能强化上限 15%（基础≥15 不再受益，但不削减）
AWK_ATK = 0.20         # 攻/魔 +1%×20次=+20%（全员同幅，只抬绝对DPS不改排名）

def awaken_speed(sec):
    """觉醒后行动间隔：扁平-2秒，下限3sec；已≤3的角色无收益。"""
    return max(sec - AWK_SPEED_SEC, AWK_SPEED_FLOOR, 0.1)

def awaken_charge(pct):
    """觉醒后必杀充填量：+6pt 封顶15%；基础≥15 保持原值。"""
    return pct if pct >= AWK_CHARGE_CAP else min(pct + AWK_CHARGE, AWK_CHARGE_CAP)
R_ref = 0.50           # 固定防御率（Step3 用户确认=0.50，古纳冈类；可一行改 0.60/0.75）
STAMINA_DRAIN = 0.02
COMBO_THRESHOLD = 60.0 # 连击率≥60% 视为"连击输出型"（Step3 用户确认）

# 7 BOSS 减伤率（reco-team.md v0.3，源 raid.md）——用于 Part2 适配层
BOSS_R = {
    '黄金甜心': 0.50, '古纳冈': 0.50, '乌塔尔': 0.65,
    '堕威大佛': 0.60, '大往女': 0.60, '狂王': 0.60, '弗栗多': 0.75,
}

# ---------- 文本解析工具 ----------
def norm(t):
    return (t or '').replace('％', '%')
DOWN_VERB = r'(?:ダウン|を下|下降|低下|減少|降低|下げ|下)'
UP_VERB = r'(?:アップ|上昇|上がる|上升|提升|増)'
def _near(text, pos, win=44):
    return text[pos:pos+win]

def parse_def_down(text):
    t = norm(text); best = 0.0
    for kw in ('防御', '攻防', '防速'):
        for m in re.finditer(kw + r'.{0,16}?(\d+)%', t):
            if re.search(DOWN_VERB, _near(t, m.start())):
                best = max(best, int(m.group(1)))
    for m in re.finditer(r'防御.{0,10}?(\d+)%.{0,8}?(降低|下降|减少)', t):
        best = max(best, int(m.group(1)))
    return min(1.0, best / 100.0)

def parse_atk_buff(text):
    t = norm(text); best = 0.0
    for m in re.finditer(r'攻撃力?.{0,12}?(\d+)%', t):
        if re.search(UP_VERB, _near(t, m.start())):
            best = max(best, int(m.group(1)))
    return best / 100.0

def parse_dmg_up(text):
    t = norm(text); best = 0.0
    for m in re.finditer(r'与.{0,10}?ダメ.{0,14}?(\d+)%', t):
        if re.search(UP_VERB, _near(t, m.start())):
            best = max(best, int(m.group(1)))
    for m in re.finditer(r'ダメージ.{0,8}?(\d+)%', t):
        if re.search(UP_VERB, _near(t, m.start())):
            best = max(best, int(m.group(1)))
    return best / 100.0

def parse_guard(text):
    t = norm(text); best = 0.0
    for m in re.finditer(r'防御.{0,10}?(\d+)%', t):
        if re.search(UP_VERB, _near(t, m.start())):
            best = max(best, int(m.group(1)))
    for m in re.finditer(r'与.{0,10}?ダメ.{0,14}?(\d+)%', t):
        if re.search(DOWN_VERB, _near(t, m.start())):
            best = max(best, int(m.group(1)))
    return min(1.0, best / 100.0)

def parse_speed(text):
    t = norm(text); best = 0.0
    for m in re.finditer(r'速度.{0,10}?(\d+)%', t):
        if re.search(UP_VERB, _near(t, m.start())):
            best = max(best, int(m.group(1)))
    return best / 100.0

def parse_ult(text):
    """必杀倍率：只认 canon 形式「敵(単体|横一列|全体)...X倍」。
    防错：排除「人数×N%必杀技威力アップ」类团队缩放 buff。"""
    t = norm(text); mult = 0; aoe = False; tgt = ''
    for m in re.finditer(r'敵(単体|横一列|全体).{0,30}?(\d+)倍', t):
        v = int(m.group(2)); mult = max(mult, v)
        if m.group(1) == '全体':
            aoe = True
        tgt = m.group(1)
    for m in re.finditer(r'必殺威力×(\d+)', t):   # 严格兜底
        mult = max(mult, int(m.group(1)))
    return mult, aoe, tgt

def has(text, *pats):
    t = norm(text)
    return any(re.search(p, t, re.IGNORECASE) for p in pats)

HEAL = (r'回復', r'回复', r'治癒', r'回血')
IMMUNE = (r'無効', r'免疫', r'不受影响')
NO_RETREAT = (r'撤退しない', r'撤退しなく', r'不会撤退')
REVIVE = (r'蘇生', r'復活', r'生き返', r'复活')
HARDCC = (r'スタン', r'魅了', r'呪縛', r'束縛', r'眩晕', r'魅惑', r'束缚')
DEC_CC = (r'異常を回復', r'異常状態を回復', r'異常を治', r'異常を取り除', r'解除', r'净化')
SLOW = (r'速度低下', r'速度ダウン', r'速度降低', r'速度を下', r'速度を減')

# ---------- 单角色特征解析（叠加固定觉醒强化 + 真实战斗细节） ----------
def kit_of(rec):
    parts = []
    for u in (rec.get('ultimates') or []):
        parts.append(u.get('eff_ja', '') + ' ' + u.get('eff_zh', ''))
    for u in (rec.get('uniques') or []):
        parts.append(u.get('eff_ja', '') + ' ' + u.get('eff_zh', ''))
    text = ' '.join(parts)
    st = rec.get('stats_lv100') or {}
    cm = rec.get('combat') or {}
    atk = st.get('攻撃力') or 0
    mag = st.get('魔法力') or 0
    ult_mult, aoe, tgt = parse_ult(text)
    raw_combo = cm.get('combo_rate') or 0.0          # 真实连击率(%)
    combo_rate = raw_combo / 100.0                    # 公式用小数(0.30)
    action_speed = cm.get('action_speed_sec') or 5.0
    ult_charge = cm.get('ult_charge') or 7.5
    return {
        'name': rec['name'], 'rarity': str(rec.get('rarity')),
        'atk_type': rec.get('atk_type', ''),
        'base': max(atk, mag),
        'ult_mult': ult_mult or 1, 'aoe': aoe, 'tgt': tgt,
        'def_down': parse_def_down(text),
        'atk_buff': parse_atk_buff(text),
        'dmg_up': parse_dmg_up(text),
        'guard': parse_guard(text),
        'self_speed': parse_speed(text),          # 自身速度buff（若有）
        'combo_rate': combo_rate,                 # 小数(0.30)
        'combo_rate_pct': raw_combo,              # 百分数(30)，用于显示/判定
        'action_speed': action_speed,             # 真实行动间隔(秒)
        'ult_charge': ult_charge,                 # 真实必杀充填量(%)
        'is_combo': raw_combo >= COMBO_THRESHOLD,
        'heal': has(text, *HEAL), 'immune': has(text, *IMMUNE),
        'no_retreat': has(text, *NO_RETREAT), 'revive': has(text, *REVIVE),
        'hardcc': has(text, *HARDCC), 'dec_cc': has(text, *DEC_CC),
        'slow': has(text, *SLOW),
    }

KIT = {n: kit_of(r) for n, r in BY.items()}

# ---------- 损伤频率模型 ----------
def combo_mult(cr):
    """连击伤害倍率：1 + Σ 連撃率ⁿ×decay(n)，decay=0.8/0.6/0.4/0.3(≥4击)。"""
    p = min(cr, 0.95)
    if p <= 0:
        return 1.0
    extra = (p * 0.8 + p**2 * 0.6 + p**3 * 0.4
             + 0.3 * p**4 / (1 - p))   # p⁴+p⁵+... = p⁴/(1-p)
    return 1.0 + extra

def dps_of(k, team=None):
    """单角色 DPS（team=None 用自身；team=聚合buff用队伍上下文）。"""
    # 队伍级聚合 buff（取队伍内最大值）
    atk_buff = (team['max_atk'] if team else k['atk_buff'])
    dmg_up = (team['max_dmg'] if team else k['dmg_up'])
    def_down_t = (team['def_down_t'] if team else min(1.0, k['def_down']))
    hardcc = (team['hardcc'] if team else k['hardcc'])
    # 暴击：有攻击buff（腰带+50%全员常驻）→ 稳定触发（全员一致，不影响相对排名）
    crit_on = (atk_buff > 0) or (EQ_BELT_ATK > 0)
    crit = CRIT if crit_on else 1.0
    break_m = BREAK if hardcc else 1.0
    # 削减系数（降防只剩角色 kit 自带）
    red_coeff = 1 - R_ref * (1 - def_down_t)
    # 行动间隔（觉醒扁平-2秒下限3sec → 火箭-50%百分比缩短 → 自身速度buff）
    self_speed = (k['self_speed'] if not team else 0)
    interval = awaken_speed(k['action_speed']) * (1 - EQ_ROCKET_SPEED) / (1 + self_speed)
    # 连击拖慢行动周期 → 必杀/普攻节奏变慢
    interval_ult = interval * (1 + k['combo_rate'])
    atks_per_s = 1.0 / interval_ult
    charge_eff = awaken_charge(k['ult_charge'])
    ult_casts_per_s = (charge_eff / 100.0) / interval_ult
    # 基础单击伤害（含觉醒攻+20%/腰带+50%/攻buff/增伤/削减；不含FEVER/击破/必杀倍率）
    base_hit = (k['base'] * (1 + AWK_ATK) * (1 + atk_buff + EQ_BELT_ATK)
                * (1 + dmg_up) * red_coeff)
    base_hit_crit = base_hit * crit                 # 基础单击（暴击）
    base_hit_nocrit = base_hit                      # 连击追加（不暴击）
    cm = combo_mult(k['combo_rate'])
    # 普攻 DPS：基础单击(暴击) + 连击追加(不暴击) × combo_mult
    normal_dps = (base_hit_crit + base_hit_nocrit * (cm - 1.0)) * atks_per_s
    # 必杀 DPS：基础单击 × 必杀倍率 × FEVER × 击破 × 频率
    ult_dps = base_hit * k['ult_mult'] * FEVER * break_m * ult_casts_per_s
    return normal_dps + ult_dps

def util_raw(k):
    return (100*k['revive'] + 60*k['no_retreat'] + 40*k['immune'] + 35*k['heal']
            + 30*k['dec_cc'] + 25*k['hardcc'] + 30*k['guard'])

max_dps = max(dps_of(k) for k in KIT.values())
max_util = max(util_raw(k) for k in KIT.values())

def strength(k):
    dn = dps_of(k) / max_dps * 100
    un = util_raw(k) / max_util * 100
    return 0.70 * dn + 0.30 * un, dn, un

SCORES = {n: strength(KIT[n]) for n in KIT}
ranked = sorted(SCORES, key=lambda n: -SCORES[n][0])

def tier_of(rank_idx, total):
    p = rank_idx / total
    if p < 0.10: return 'T0'
    if p < 0.30: return 'T1'
    if p < 0.60: return 'T2'
    return 'T3'

print('=' * 118)
print('v0.8 单角色固定强度量化模型（RAID 专用 · 真实频率公式 · 真实觉醒表 · 真实两件配装）')
print('=' * 118)
print('范围：仅 raid（B宇宙/广域战/全域战 暂占位）。场景全固定 → 强度只取决于角色 kit + 真实战斗细节。')
print(f'固定场景：BOSS 机制常亮·固定伤害·体力-2%/s·固定防御率 R={R_ref} | 角色 满星100级·觉醒+·觉醒属性强化满(真实表)·两件主装')
print(f'真实数据：行動速度(秒)/必殺充填量(%)/連撃率 来自 char_data.json.combat')
print(f'常数 FEVER={FEVER} CRIT={CRIT} BREAK={BREAK} 装备 火箭速-{EQ_ROCKET_SPEED:.0%}/腰带攻魔+{EQ_BELT_ATK:.0%}（副装/纳豆已删，避免多变量）')
print(f'觉醒强化(真实表) 速-{AWK_SPEED_SEC:.0f}s(下限{AWK_SPEED_FLOOR:.0f}s)/充+{AWK_CHARGE:.0f}pt(上限{AWK_CHARGE_CAP:.0f}%)/攻魔+{AWK_ATK:.0%} 连击阈值{COMBO_THRESHOLD:.0f}%')
print(f'总角色 {len(DATA)} · maxDPS={max_dps:,.0f} · maxUTIL={max_util:,.0f}')

print('\n' + '=' * 118)
print('【raid 通用强度 TOP 40（固定分，BOSS无关）→ 任何 raid BOSS 初筛直接套用】')
print('=' * 118)
print(f'{"#":>3} {"角色":<26} {"稀有":<4} {"强度":>6} {"档":>3} {"DPS分":>6} {"辅分":>6}  关键特征')
for i, n in enumerate(ranked[:40], 1):
    k = KIT[n]; s, dn, un = SCORES[n]
    feats = []
    if k['def_down']: feats.append(f"降防{k['def_down']:.0%}")
    if k['ult_mult'] >= 6: feats.append(f"必杀×{k['ult_mult']}")
    if k['atk_buff']: feats.append(f"攻{k['atk_buff']:.0%}")
    if k['dmg_up']: feats.append(f"增{k['dmg_up']:.0%}")
    if k['is_combo']: feats.append(f"连击{k['combo_rate']:.0%}")
    if k['revive']: feats.append("复活")
    if k['no_retreat']: feats.append("不撤")
    if k['immune']: feats.append("免疫")
    if k['heal']: feats.append("奶")
    if k['hardcc']: feats.append("硬控")
    print(f'{i:>3} {n:<26} {k["rarity"]:<4} {s:>6.1f} {tier_of(i-1,len(ranked)):>3} {dn:>6.1f} {un:>6.1f}  ' + ' '.join(feats))

print('\n' + '=' * 118)
print('【分档统计（T0/T1/T2/T3 人数 & 稀有度构成）】')
print('=' * 118)
tier_counts = defaultdict(lambda: defaultdict(int))
for i, n in enumerate(ranked):
    t = tier_of(i, len(ranked))
    tier_counts[t][KIT[n]['rarity']] += 1
    tier_counts[t]['__all__'] += 1
for t in ['T0', 'T1', 'T2', 'T3']:
    c = tier_counts[t]
    print(f'  {t}: 共{c["__all__"]:>3}  [SSR {c.get("SSR",0):>3} / SR {c.get("SR",0):>3} / R {c.get("R",0):>3}]')

print('\n' + '=' * 118)
print('【稀缺职能 × 强度：降防/不撤退/复活/免疫 高分持有者（配队优先占槽）】')
print('=' * 118)
for role, key in [('降防','def_down'), ('不撤退','no_retreat'), ('复活','revive'), ('免疫','immune')]:
    holders = [n for n in ranked if KIT[n][key]][:12]
    print(f'  [{role}] ' + '、'.join(f'{n}({SCORES[n][0]:.0f}/{KIT[n]["rarity"]})' for n in holders))

print('\n' + '=' * 118)
print('【連撃输出型（连击率≥阈值）必杀/普攻拆解：验证"必杀权重下降"】')
print('=' * 118)
combo_out = sorted([n for n in ranked if KIT[n]['is_combo']], key=lambda n: -SCORES[n][0])
if combo_out:
    print(f'  {"角色":<26} {"稀有":<4} {"连击率":>6} {"间隔s":>6} {"充填%":>6}  必杀DPS  普攻DPS  必杀占比')
    for n in combo_out:
        k = KIT[n]
        # 拆解
        interval = awaken_speed(k['action_speed']) * (1 - EQ_ROCKET_SPEED) / (1 + k['self_speed'])
        interval_ult = interval * (1 + k['combo_rate'])
        atks = 1/interval_ult
        charge_eff = awaken_charge(k['ult_charge'])
        ucps = (charge_eff/100)/interval_ult
        red = 1 - R_ref*(1 - min(1.0, k['def_down']))
        crit = CRIT if (k['atk_buff']>0 or EQ_BELT_ATK>0) else 1.0
        break_m = BREAK if k['hardcc'] else 1.0
        base_hit = k['base']*(1+AWK_ATK)*(1+k['atk_buff']+EQ_BELT_ATK)*(1+k['dmg_up'])*red
        cm = combo_mult(k['combo_rate'])
        ndps = (base_hit*crit + base_hit*(cm-1))*atks
        udps = base_hit*k['ult_mult']*FEVER*break_m*ucps
        tot = ndps+udps
        print(f'  {n:<26} {k["rarity"]:<4} {k["combo_rate_pct"]:>5.0f}% {k["action_speed"]:>6.1f} {k["ult_charge"]:>6.1f}  {udps:>9,.0f} {ndps:>9,.0f} {udps/tot:>6.1%}')
else:
    print('  （无连击率≥阈值的输出角色）')

# =================== Part2：推荐 4 队 · raid 考试打分 ===================
print('\n' + '=' * 118)
print('【Part2：推荐 5 人队 · raid 伤害公式考试打分（固定场景 + 7 BOSS 适配层）】')
print('=' * 118)
TEAMS = {
    'A. 顶配均衡队': ['エスカサファイア・ムーンライズ', '小鬼の斗羽大洋', 'ダンスクイーン・ピカ', '超昂閃忍ナリカ', 'FM77'],
    'B. 新手友好队': ['ビートノーブル・カノン', '閃忍フクシュウチャン', 'ビートアミュレット・ノノノ', 'FM77', 'ビートアイドル・タマキ'],
    'C. 高难raid居座队': ['エスカサファイア・ムーンライズ', '小鬼の斗羽大洋', 'ダンスクイーン・ピカ', 'ブライドハルカ・リバース', '超昂閃忍ナリカ'],
    'D. 暴力输出队': ['レジェンド・ハルカ', '幻忍コテツ', '黒門天・屍寺炎斎', 'ブライド・スバル', '閃忍ワーグ'],
}

def team_aggregate(names):
    ks = [KIT[n] for n in names]
    max_def = max((k['def_down'] for k in ks), default=0)
    max_atk = max((k['atk_buff'] for k in ks), default=0)
    max_dmg = max((k['dmg_up'] for k in ks), default=0)
    def_down_t = min(1.0, max_def)
    atk_mult = 1 + max_atk + EQ_BELT_ATK
    dmg_up_mult = 1 + max_dmg
    hardcc = any(k['hardcc'] for k in ks)
    flags = {
        'heal': any(k['heal'] for k in ks), 'immune': any(k['immune'] for k in ks),
        'no_retreat': any(k['no_retreat'] for k in ks), 'revive': any(k['revive'] for k in ks),
        'aoe': any(k['aoe'] for k in ks), 'hardcc': hardcc,
        'dec_cc': any(k['dec_cc'] for k in ks), 'slow': any(k['slow'] for k in ks),
    }
    return dict(max_def=max_def, max_atk=max_atk, max_dmg=max_dmg, def_down_t=def_down_t,
                atk_mult=atk_mult, dmg_up_mult=dmg_up_mult, hardcc=hardcc, flags=flags)

def fit_mult(boss, agg):
    f = agg['flags']
    if boss == '乌塔尔':   return 1.0 if f['aoe'] else 0.60
    if boss == '狂王':     return 1.0 if f['aoe'] else 0.70
    if boss == '堕威大佛': return 1.0 if (f['hardcc'] or f['aoe']) else 0.70
    if boss == '大往女':   return 1.0 if (f['immune'] or f['dec_cc']) else 0.80
    if boss == '古纳冈':   return 1.0 if f['heal'] else 0.65
    if boss == '弗栗多':
        m = 1.0
        if f['slow']: m += 0.10
        if f['no_retreat']: m += 0.05
        return m
    return 1.0

def team_dps_vs(names, agg, boss):
    R = BOSS_R[boss]
    eff_R = R * (1 - agg['def_down_t'])
    red_coeff = 1 - eff_R
    team_buff = {
        'max_atk': agg['max_atk'], 'max_dmg': agg['max_dmg'],
        'def_down_t': min(1.0, agg['def_down_t']), 'hardcc': agg['hardcc'],
    }
    dmg = 0.0
    for n in names:
        k = KIT[n]
        # 用队伍聚合 red_coeff 重算（队伍 def_down 覆盖单角色）
        interval = awaken_speed(k['action_speed']) * (1 - EQ_ROCKET_SPEED) / (1 + k['self_speed'])
        interval_ult = interval * (1 + k['combo_rate'])
        atks = 1/interval_ult
        charge_eff = awaken_charge(k['ult_charge'])
        ucps = (charge_eff/100)/interval_ult
        atk_buff = agg['max_atk']; dmg_up = agg['max_dmg']
        crit = CRIT if (atk_buff > 0 or EQ_BELT_ATK > 0) else 1.0
        break_m = BREAK if agg['hardcc'] else 1.0
        base_hit = k['base']*(1+AWK_ATK)*(1+atk_buff+EQ_BELT_ATK)*(1+dmg_up)*red_coeff
        cm = combo_mult(k['combo_rate'])
        ndps = (base_hit*crit + base_hit*(cm-1))*atks
        udps = base_hit*k['ult_mult']*FEVER*break_m*ucps
        dmg += ndps + udps
    return dmg, red_coeff

results = {}
for tname, names in TEAMS.items():
    agg = team_aggregate(names)
    print('\n' + '-' * 118)
    print(f'【{tname}】  成员强度分: ' + ' / '.join(f'{n}({SCORES[n][0]:.0f})' for n in names))
    print(f"    降防 max{agg['def_down_t']:.0%}(仅角色kit)  "
          f"攻buff×{agg['atk_mult']:.2f}(含腰带+{EQ_BELT_ATK:.0%})  增伤×{agg['dmg_up_mult']:.2f}  "
          f"暴击{CRIT if (agg['max_atk']>0 or EQ_BELT_ATK>0) else 1.0:.2f} 击破{BREAK if agg['hardcc'] else 1.0:.2f}")
    f = agg['flags']
    print(f"    对策flag: 治疗{'✓' if f['heal'] else '✗'} 免疫{'✓' if f['immune'] else '✗'} 不撤退{'✓' if f['no_retreat'] else '✗'} "
          f"复活{'✓' if f['revive'] else '✗'} 全体{'✓' if f['aoe'] else '✗'} 硬控{'✓' if f['hardcc'] else '✗'} 解控{'✓' if f['dec_cc'] else '✗'} 减速{'✓' if f['slow'] else '✗'}")
    print(f"    {'BOSS':<8} {'减伤率':>6} {'降防后有效减伤':>13} {'削减系数':>8} {'适配':>5} {'DPS(秒伤)':>16} {'最终得分':>14}")
    res = {}
    for boss in BOSS_R:
        raw, red = team_dps_vs(names, agg, boss)
        fm = fit_mult(boss, agg)
        final = raw * fm
        res[boss] = (raw, final, red, fm)
        print(f"    {boss:<8} {BOSS_R[boss]:>5.0%} {BOSS_R[boss]*(1-agg['def_down_t']):>12.0%} {red:>7.2f} {fm:>4.2f} {raw:>16,.0f} {final:>14,.0f}")
    results[tname] = res

print('\n' + '=' * 118)
print('【考试排名：每 BOSS 按最终得分 T0>T1>T2>T3】')
boss_rank = {}
for boss in BOSS_R:
    order = sorted(TEAMS.keys(), key=lambda t: -results[t][boss][1])
    boss_rank[boss] = order
    line = ' > '.join(f'{t.split(".")[0]} [{results[t][boss][1]:,.0f}]' for t in order)
    print(f'  {boss:<8}: {line}')

rank_sum = {t: 0 for t in TEAMS}
for boss in BOSS_R:
    for i, t in enumerate(boss_rank[boss]):
        rank_sum[t] += i
print('\n【综合名次和（越小越强）】')
for t in sorted(TEAMS, key=lambda x: rank_sum[x]):
    avg = sum(results[t][b][1] for b in BOSS_R)/len(BOSS_R)
    print(f'  {t:<22} 名次和={rank_sum[t]}  平均得分={avg:,.0f}')

# =================== 终局副本 4 模式占位 ===================
print('\n' + '=' * 118)
print('【终局副本 4 模式 · 量化模型占位】')
print('=' * 118)
print(f'  [raid]      ← 本模型已攻破（固定场景：机制常亮/固定伤害/体力-2%/s/固定防御 R={R_ref:.2f}）')
print('  [B宇宙]     ← 占位：待接入（同框架：固定其场景常量即可复用）')
print('  [广域战]    ← 占位：待接入')
print('  [全域战]    ← 占位：待接入')
print('说明：四模式共用本「单角色 kit → 强度分」内核；差异仅在场景常数。raid 跑通后其余三模式只需替换常数块 + 适配层。')

print('\n可复用性：新增角色 → 在 char_data.json 补充 → 重跑本脚本 → 自动进入 TOP40/分档/队伍打分。')
print('总角色数:', len(DATA))
