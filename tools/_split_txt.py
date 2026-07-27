import os
import re
import shutil

BASE = r"d:\D11_DeveloperProject\150_HTML_Project\escalation_heroines\escah\tools\_texts_for_translation"
RECYCLE = r"d:\D11_DeveloperProject\150_HTML_Project\escalation_heroines\escah\recycle_bin\tools\_texts_for_translation"
LIMIT = 26000  # 单文件字符上限（含空白/换行）

KEY_RE = re.compile(r'(?m)^\s*\[\d+\]')
PART_RE = re.compile(r'-\d+$')  # 已切分的 -N 片段跳过，避免重复处理


def read_text(p):
    try:
        return open(p, encoding="utf-8").read()
    except UnicodeDecodeError:
        return open(p, encoding="utf-8-sig").read()


def split_blocks(text):
    """按 key 切成块，每块从 [N] 起到下一个 [N] 之前，保留原始字符。"""
    starts = [m.start() for m in KEY_RE.finditer(text)]
    if not starts:
        return [text]
    blocks = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(text)
        blocks.append(text[s:e])
    return blocks


def chunk_blocks(blocks):
    """累计字符，遇到下一个 key 会越过 LIMIT 则先把当前块落盘。"""
    chunks, cur, cur_len = [], [], 0
    for b in blocks:
        if cur and cur_len + len(b) > LIMIT:
            chunks.append("".join(cur))
            cur, cur_len = [], 0
        cur.append(b)
        cur_len += len(b)
    if cur:
        chunks.append("".join(cur))
    return chunks


def main():
    split_files = []      # (relpath, n_parts)
    oversized = []        # 单 key 就超 26000，无法切分
    for root, _, files in os.walk(BASE):
        for f in files:
            if not f.lower().endswith(".txt"):
                continue
            stem = f[:-4]
            if PART_RE.search(stem):      # 已是 XXX-N.txt，跳过
                continue
            p = os.path.join(root, f)
            text = read_text(p)
            if len(text) <= LIMIT:
                continue
            rel = os.path.relpath(p, BASE)
            chunks = chunk_blocks(split_blocks(text))
            if len(chunks) <= 1:
                oversized.append((rel, len(text)))
                continue
            # 写出 XXX-1.txt, XXX-2.txt ...
            for i, c in enumerate(chunks, 1):
                outp = os.path.join(root, f"{stem}-{i}.txt")
                with open(outp, "w", encoding="utf-8") as fh:
                    fh.write(c)
            # 原文件移入 recycle_bin（不删除）
            dest = os.path.join(RECYCLE, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(p, dest)
            split_files.append((rel, len(chunks)))
            print(f"切分 {rel} -> {len(chunks)} 个片段")

    print(f"\n完成：{len(split_files)} 个文件被切分")
    for rel, n in split_files:
        print(f"  {rel}: {n} 片")
    if oversized:
        print(f"\n⚠️ {len(oversized)} 个文件因单个 key 已超 {LIMIT} 字符，无法不破坏 key 地切分，原文件保留：")
        for rel, n in oversized:
            print(f"  {rel}: {n} 字符")


if __name__ == "__main__":
    main()
