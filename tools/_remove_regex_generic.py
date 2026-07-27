"""一次性 AST 移除 zh_patch.py 中的 REGEX_RULES / GENERIC / _GENERIC_ORDERED 及其 patch() 调用。"""
import ast
import pathlib

SRC = pathlib.Path("tools/zh_patch.py")
text = SRC.read_text(encoding="utf-8")
tree = ast.parse(text)
lines = text.splitlines(keepends=True)

# 1) 收集要删除的 Assign / AnnAssign 顶层节点：REGEX_RULES, GENERIC, _GENERIC_ORDERED
to_remove_ranges = []
target_names = {"REGEX_RULES", "GENERIC", "_GENERIC_ORDERED"}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id in target_names:
                to_remove_ranges.append((node.lineno, node.end_lineno))
    elif isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name) and node.target.id in target_names:
            to_remove_ranges.append((node.lineno, node.end_lineno))

# 2) patch() 函数体内删除对 REGEX_RULES / _GENERIC_ORDERED 的两个 for 循环
patch_func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "patch")
loop_ranges = []
for stmt in patch_func.body:
    if isinstance(stmt, ast.For):
        # 判断：REGEX_RULES 循环（遍历元组）或 _GENERIC_ORDERED 循环（带 in text 判断）
        t = stmt.target
        iter_src = ast.dump(stmt.iter)
        if "REGEX_RULES" in iter_src:
            loop_ranges.append((stmt.lineno, stmt.end_lineno))
        elif "GENERIC_ORDERED" in iter_src:
            loop_ranges.append((stmt.lineno, stmt.end_lineno))

# 合并所有删除区间，按行号倒序删除，并清理多余空行
ranges = sorted(to_remove_ranges + loop_ranges, reverse=True)

# 标记要删除的行（1-based）
del_lines = set()
for (lo, hi) in ranges:
    for ln in range(lo, hi + 1):
        del_lines.add(ln)

new_lines = [ln for i, ln in enumerate(lines, start=1) if i not in del_lines]

# 折叠连续空行（>2 个连续空行压成 2 个）
out = []
blank = 0
for ln in new_lines:
    if ln.strip() == "":
        blank += 1
        if blank <= 2:
            out.append(ln)
    else:
        blank = 0
        out.append(ln)

SRC.write_text("".join(out), encoding="utf-8")
print("removed ranges:", ranges)
print("done")
