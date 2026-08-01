"""抽取指定候选角色的完整 必杀技/固有效果 文本，供大模型核实机制幅度与条件。"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = json.load(open('llm_reco/char_data.json', encoding='utf-8'))
by = {d['name']: d for d in data}

focus = [
    # 生存/不撤退
    'ビートソニック・アキレス', 'ブライドハルカ・リバース', 'FM77', '閃忍マユリ',
    '神騎フローレル', '真夏のハルカ', '超昂閃忍ナリカ', '体育祭のヤブルー',
    # 速度/充能辅助
    '閃忍サイカ', '神騎アルゴル', '妹の1024', 'ビートアミュレット・ノノノ',
    # 稀有buff辅助
    '魔女ミヤビ', '真夏のイーイー', '黒門天・屍寺炎斎',
    # 治疗+异常
    '制服ニャンコ', 'ビートプレジデント・シーラ', '魔女シズク',
    # 减益/破防/控场
    '神騎ハニーエル', '鬼の斗羽大洋', '閃忍ツルコ', '閃忍クサリ',
    # 魅惑免疫 R
    'エスカ・アメイズ', '魔女フタバ', 'バレンタインツルコ',
    # 其他强包
    '閃忍ニャンコ', '六の法杖セラフィール', 'アイドルの奉輪こもり',
]

for name in focus:
    d = by.get(name)
    if not d:
        print(f'### {name} :: NOT FOUND'); continue
    print('=' * 90)
    print(f"### {name}  | {d.get('rarity')} | {d.get('faction')} | {d.get('atk_type')}")
    print(f"    体/攻/防/魔/魔抗 = {d.get('stats_lv100')}")
    print('--- 固有效果 ---')
    for u in d.get('uniques', []):
        print(f"  * {u.get('name_zh') or u.get('name_ja')}")
        print(f"    ja: {u.get('eff_ja')}")
        print(f"    zh: {u.get('eff_zh')}")
    print('--- 必杀技 ---')
    for u in d.get('ultimates', []):
        print(f"  * {u.get('name_zh') or u.get('name_ja')}")
        print(f"    ja: {u.get('eff_ja')}")
        print(f"    zh: {u.get('eff_zh')}")
