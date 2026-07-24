import ast, pathlib, json, sys

# 通用注入器：读取一个 JSON 文件（[ [ja, zh], ... ]），
# 过滤掉 zh_patch.py 中已存在的 JA2ZH key，插入到 JA2ZH 字典开头。
src = pathlib.Path(__file__).resolve().parent / 'zh_patch.py'
text = src.read_text(encoding='utf-8')
tree = ast.parse(text)
existing = set()
for node in ast.walk(tree):
    tgt = None
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == 'JA2ZH':
                tgt = node
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == 'JA2ZH':
        tgt = node
    if tgt is not None and isinstance(tgt.value, ast.Dict):
        for k in tgt.value.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                existing.add(k.value)

batch_file = sys.argv[1]
label = sys.argv[2] if len(sys.argv) > 2 else batch_file
BATCH = json.loads(pathlib.Path(batch_file).read_text(encoding='utf-8'))
new = [b for b in BATCH if b[0] not in existing]
lines = [f"    # ---- {label} ----"]
for ja, zh in new:
    lines.append("    " + json.dumps(ja, ensure_ascii=False) + ": " + json.dumps(zh, ensure_ascii=False) + ",")
block = "\n".join(lines) + "\n"
marker = "JA2ZH: dict[str, str] = {"
idx = text.index(marker) + len(marker)
text = text[:idx] + "\n" + block + text[idx:]
src.write_text(text, encoding='utf-8')
print(f"existing={len(existing)}; batch={len(BATCH)}; added={len(new)}; skipped={len(BATCH)-len(new)}")
