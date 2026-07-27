"""一次性：把 data/parsed/characters/*.json 的 icon 字段从 wiki 原始 src（attach2/...png）
转成与本地图一致的存储名（img/<sha256[:16]>.png），使悬浮窗能显示头像。"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
from escah_pipeline.registry import _img_local_name

D = "data/parsed/characters"
n = 0
for f in os.listdir(D):
    if not f.endswith(".json"):
        continue
    p = os.path.join(D, f)
    j = json.load(open(p, encoding="utf-8"))
    ic = j.get("icon", "")
    if ic and not ic.startswith("img/"):
        j["icon"] = _img_local_name(ic)
        json.dump(j, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        n += 1
print(f"fixed {n} char json icon fields")
