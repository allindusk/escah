"""把一份「原文→译文」映射批量应用到所有存在该缺口的页面（按 ja 广播，覆盖同原文节点）。

用法：
  python tools/_dev/apply_ja_map_all.py <mapfile> [--dry]
"""
import subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _imgblk_gaps import collect  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def main():
    mapfile = sys.argv[1]
    dry = '--dry' in sys.argv
    agg = collect()
    slugs = sorted({it[0] for r in agg.values() for it in r['items']})
    print(f'涉及页面 {len(slugs)} 个，缺译节点 {sum(len(r["items"]) for r in agg.values())} 条')
    changed = 0
    for i, slug in enumerate(slugs, 1):
        cmd = [sys.executable, 'tools/_dev/apply_ja_map.py', slug, mapfile]
        if not dry:
            cmd.append('--apply')
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', cwd=str(ROOT))
        out = (r.stdout or '').strip().splitlines()
        last = out[-1] if out else (r.stderr or '').strip()[-120:]
        if '待改 0 条' not in last:
            changed += 1
            print(f'  [{i}/{len(slugs)}] {slug}: {last}')
    print(f'完成：{changed} 页有改动')


main()
