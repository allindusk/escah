import json, glob, os, re

OUT_DIR = 'tools/_todo_translate'
TARGET_LINES = 700   # 期望每个文件约这么多行(角色块不跨文件)
HARD_CAP = 1500      # 单文件硬上限;单个角色块超过则独占下一文件

SECTION_TITLES = {
    '基本情報','プロフィール','性格','設定','ボイス','ゲームにおいて','小ネタ',
    '公式ツイッターの紹介','関連イラスト','コメントフォーム','関連記事','備考',
    'データ','ステータス','スキル','覚醒','限界突破','専用装備','回想','エピソード',
    '登場ストーリー','ボイス一覧','台詞','セリフ',
}

# ボイス 模块里的"分类标签"(会話1/戦闘開始1/捕縛 等)不是台词，排除
LABEL_RE = re.compile(
    r'^(通常攻撃|必殺技|被ダメージ|戦闘開始|戦闘参加|戦闘勝利|レベルアップ|固有効果発動|アイテム使用|好感度アイテム・限界突破アイテム使用)\d+'
    r'|^会話\d+\(変身[前後]\)'
    r'|^放置\d+\(変身[前後]\)'
    r'|^(加入|捕縛|撤退|エネミー版ボイス|変身前は存在しない。)$'
)
# 系统注记(非台词)，排除
NOTE_RE = re.compile(r'^[-－]?（?常時発動型')
SKIP_EXACT = {'クリックでセリフ一覧を開く', 'エネミー版ボイス', '変身前は存在しない。'}

def is_label(ja):
    if ja in SKIP_EXACT:
        return True
    if NOTE_RE.match(ja):
        return True
    return bool(LABEL_RE.match(ja))

def find_voice_region(e):
    keys = [k for k in e if k != '_blocks']
    voice_start = None
    for i, k in enumerate(keys):
        v = e[k]
        ja = (v.get('ja', '') if isinstance(v, dict) else '').strip()
        if ja == 'ボイス':
            nxt = (e[keys[i+1]].get('ja', '') if i+1 < len(keys) else '')
            if 'クリックでセリフ一覧' in nxt:
                voice_start = i
                break
    if voice_start is None:
        cand = [i for i, k in enumerate(keys)
                if (e[k].get('ja', '') if isinstance(e[k], dict) else '').strip() == 'ボイス']
        if cand:
            voice_start = cand[-1]
    if voice_start is None:
        return None
    end = len(keys)
    for j in range(voice_start + 1, len(keys)):
        ja = (e[keys[j]].get('ja', '') if isinstance(e[keys[j]], dict) else '').strip()
        if ja in SECTION_TITLES and ja != 'ボイス':
            end = j
            break
    return keys[voice_start + 2:end]  # 跳过 ボイス 标题 + UI提示

# 全局去重：line_ja -> {n, refs:[(stem,key)]}
line_map = {}
order = []          # 首次出现的 line_ja 顺序
char_blocks = []    # [(stem, [line_ja,...])]
n_no_voice = 0

for p in sorted(glob.glob('data/parsed/i18n/characters/*.json')):
    stem = os.path.splitext(os.path.basename(p))[0]
    try:
        e = json.loads(open(p, encoding='utf-8').read())
    except Exception:
        continue
    region = find_voice_region(e)
    if not region:
        n_no_voice += 1
        continue
    block = []
    for k in region:
        v = e[k]
        ja = (v.get('ja', '') if isinstance(v, dict) else '').strip()
        if not ja or is_label(ja):
            continue
        if ja in line_map:
            line_map[ja]['refs'].append((stem, k))
        else:
            line_map[ja] = {'refs': [(stem, k)]}
            order.append(ja)
            block.append(ja)
    if block:
        char_blocks.append((stem, block))

# 分配全局编号 N
for i, ja in enumerate(order, 1):
    line_map[ja]['n'] = i

# 按角色打包（角色块不跨文件;目标行数 TARGET,硬上限 HARD_CAP）
files = []
cur = []
for stem, block in char_blocks:
    if cur and (len(cur) + len(block) > TARGET_LINES) and len(cur) <= HARD_CAP:
        files.append(cur)
        cur = []
    cur.extend(block)
    if len(cur) > HARD_CAP:           # 单角色块超上限 → 独占成下一文件
        files.append(cur)
        cur = []
if cur:
    files.append(cur)

os.makedirs(OUT_DIR, exist_ok=True)
# 清掉旧产物
for f in glob.glob(os.path.join(OUT_DIR, 'voices-*.txt')):
    os.remove(f)

written = 0
mapping = {}
for fi, block in enumerate(files, 1):
    todo_path = os.path.join(OUT_DIR, f'voices-{fi}.txt')
    tr_path = os.path.join(OUT_DIR, f'voices-{fi}_translated.txt')
    lines = []
    for ja in block:
        n = line_map[ja]['n']
        lines.append(f'[{n}] {ja}')
        mapping[str(n)] = {'ja': ja, 'refs': line_map[ja]['refs']}
    open(todo_path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    open(tr_path, 'w', encoding='utf-8').close()  # 空白待填
    written += len(block)

meta = {
    '_meta': {
        'description': '角色页 ボイス 模块台词(已剔除分类标签与重复文本, 全局去重)',
        'total_unique_lines': len(order),
        'files': len(files),
        'chars_with_voice': len(char_blocks),
        'chars_without_voice': n_no_voice,
        'max_lines_per_file': HARD_CAP,
        'target_lines_per_file': TARGET_LINES,
    },
    'lines': mapping,
}
open(os.path.join(OUT_DIR, 'voices_map.json'), 'w', encoding='utf-8').write(
    json.dumps(meta, ensure_ascii=False, indent=1))
print('done')
