"""从 data/parsed/characters/*.json 抽取全部角色关键数据 -> llm_reco/char_data.json

section 结构: {'label':.., 'rows': [[cell,...], ...]}, cell = {'h':bool,'t':ja,'tr':bool,'zh':zh}
"""
import json, glob, os, re
from collections import Counter

CHAR_DIR = 'data/parsed/characters'
OUT = 'llm_reco/char_data.json'

def ja(cell):
    return (cell or {}).get('t', '') or ''
def zh(cell):
    c = cell or {}
    return (c.get('zh') or c.get('t') or '').strip()
def rows_of(section):
    return (section or {}).get('rows', []) if isinstance(section, dict) else []
def num(s):
    s = re.sub(r'[,\s]', '', s or '')
    return int(s) if s.isdigit() else None

def table_map(section):
    """返回 (header_index_map, data_rows)"""
    rws = rows_of(section)
    if len(rws) < 2:
        return {}, []
    hdr = rws[0]
    hidx = {ja(c).strip(): i for i, c in enumerate(hdr)}
    return hidx, rws[1:]

ATK_NORM = {
    '近战物理攻击': '近战物理',
    '近战攻击（物理）': '近战物理',
    '近距离（物理）': '近战物理',
    '远程物理攻击': '远程物理',
    '远程攻击（物理）': '远程物理',
    '长途（物理距离）': '远程物理',
    '远程魔法攻击': '远程魔法',
    '近战魔法攻击': '近战魔法',
}
def profile_info(e):
    rws = rows_of(e['sections'].get('プロフィール'))
    m = {}
    for row in rws:
        if isinstance(row, list) and len(row) >= 2:
            m[ja(row[0]).strip()] = row[1]
    faction = zh(m.get('所属勢力', ''))
    atk = ATK_NORM.get(zh(m.get('通常攻撃', '')), zh(m.get('通常攻撃', '')))
    return faction, atk

def stat_at_level(section, cols=None, target_level=None):
    hidx, data = table_map(section)
    if 'レベル' not in hidx:
        return {}
    best = {}
    for row in data:
        lvcell = row[hidx['レベル']]
        mm = re.search(r'\d+', ja(lvcell))
        if not mm:
            continue
        lv = int(mm.group())
        if cols is None:
            rec = {c: num(zh(row[i])) for c, i in hidx.items() if c != 'レベル'}
        else:
            rec = {c: num(zh(row[hidx[c]])) for c in cols if c in hidx}
        if rec:
            best[lv] = rec
    if not best:
        return {}
    if target_level is not None:
        cands = [l for l in best if l <= target_level]
        lv = max(cands) if cands else max(best)
    else:
        lv = max(best)
    return best[lv]

def first_cell(section):
    _, data = table_map(section)
    if data and data[0]:
        return zh(data[0][0])
    return ''

def effects(section):
    hidx, data = table_map(section)
    ni = hidx.get('名称'); ei = hidx.get('効果')
    if ni is None or ei is None:
        return []
    out = []
    for row in data:
        out.append({
            'name_ja': ja(row[ni]),
            'name_zh': zh(row[ni]),
            'eff_ja': ja(row[ei]),
            'eff_zh': zh(row[ei]),
        })
    return out

def detail_pairs(section):
    """詳細ステータス 是多列 label-value 对（每行可含多个 [标签,值] 对），如
    [命中力,40, 回避力,50] [連撃率,40%, 反撃率,35%] [行動速度,5sec, 必殺充填量,7.5%]。
    按"表头单元格(h=true) 后跟其值单元格"成对抽取，返回 {label_zh: raw_value}。"""
    out = {}
    for row in rows_of(section):
        if not isinstance(row, list):
            continue
        i = 0
        while i < len(row) - 1:
            if isinstance(row[i], dict) and row[i].get('h'):
                label = zh(row[i]).strip()
                val = ja(row[i + 1]).strip()
                if label:
                    out[label] = val
                i += 2
            else:
                i += 1
    return out

def parse_pct(s):
    m = re.search(r'(\d+(?:\.\d+)?)\s*%', s or '')
    return float(m.group(1)) if m else None

def parse_sec(s):
    m = re.search(r'(\d+(?:\.\d+)?)\s*sec', s or '')
    return float(m.group(1)) if m else None

def combat_detail(section):
    """抽取 raid 输出建模必需的战斗细节：连击率% / 行动速度sec / 必杀充能效率%。"""
    p = detail_pairs(section)
    return {
        'combo_rate': parse_pct(p.get('连击率')),       # %
        'action_speed_sec': parse_sec(p.get('行动速度')),  # sec，越小越快
        'ult_charge': parse_pct(p.get('必杀充能效率')),    # %
        'raw': p,
    }

def main():
    files = sorted(glob.glob(f'{CHAR_DIR}/*.json'))
    out = []
    for p in files:
        e = json.loads(open(p, encoding='utf-8').read())
        name = e.get('name', '')
        faction, atk = profile_info(e)
        rec = {
            'name': name,
            'name_zh': e.get('name_zh', '') or '',
            'rarity': e.get('rarity'),
            'faction': faction,
            'atk_type': atk,
            'obtain': first_cell(e['sections'].get('入手方法')),
            'stats_lv100': stat_at_level(e['sections'].get('基本ステータス'),
                                        ['スタミナ', '攻撃力', '防御力', '魔法力', '魔法抵抗力'], 100),
            'detail_lv100': stat_at_level(e['sections'].get('詳細ステータス'), None, 100),
            'combat': combat_detail(e['sections'].get('詳細ステータス')),
            'ultimates': effects(e['sections'].get('必殺技')),
            'uniques': effects(e['sections'].get('固有効果')),
        }
        out.append(rec)
    os.makedirs('llm_reco', exist_ok=True)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    rc = Counter(x['rarity'] for x in out if x['rarity'])
    fc = Counter(x['faction'] for x in out if x['faction'])
    at = Counter(x['atk_type'] for x in out if x['atk_type'])
    print('chars:', len(out))
    print('rarity:', dict(sorted(rc.items(), key=lambda x: str(x[0]))))
    print('faction top:', dict(fc.most_common(8)))
    print('atk_type top:', dict(at.most_common(8)))

if __name__ == '__main__':
    main()
