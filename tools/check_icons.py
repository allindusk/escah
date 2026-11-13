# -*- coding: utf-8 -*-
"""注册表头像体检：pages.yaml 里的 icon 是否都能在 data/assets/img 找到对应文件。

为什么需要（2026-11-13 实测）：
  原站角色一览的头像改成懒加载写法（`data-src=真实地址` + `src=data:…占位`），
  旧代码只读 src → 把占位符算成哈希 `560a481d94b94be2.webp` 写进注册表 →
  ハロウィンミヤビ / メイドハータン 两页头像 404，且 CI 全程静默通过。
  根因已分别在 `registry.extract_char_rows`（读 data-src）与
  `parser_puki._rewrite_images`（把 data-src 登记进 pending_assets 供下载）修掉；
  本脚本是**回归护栏**：以后任何原因导致 icon 指向不存在的文件，CI 都会告警。

判据是「文件是否存在」而不是「内容是否真实图片」：CI 的 checkout 不拉 LFS 内容，
data/assets/img 下是 LFS 指针文本，但指针存在即说明图已入库（下载过、提交过），
对「有没有这张图」这个问题的答案就是「有」。

用法：
  python tools/check_icons.py           # 体检并打印报告（缺失只告警，退出码 0）
  python tools/check_icons.py --strict  # 有缺失时退出码 1（本地复查用）
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline import config  # noqa: E402
from escah_pipeline.registry import load_registry  # noqa: E402


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    strict = "--strict" in sys.argv[1:]

    pages = load_registry()
    with_icon = [e for e in pages if (e.get("icon") or "").strip()]
    missing = []
    for e in with_icon:
        name = e["icon"].replace("\\", "/").rsplit("/", 1)[-1]
        if not name or not (config.ASSETS_IMG_DIR / name).is_file():
            missing.append((e.get("name"), e["icon"]))

    print(f"注册表 {len(pages)} 页，带 icon 的 {len(with_icon)} 条，"
          f"缺失图片文件 {len(missing)} 条")
    for name, icon in missing:
        print(f"  ❌ {name}: {icon}")
        # GitHub Actions 注解：会出现在 PR/run 的 Annotations 里，不阻断步骤
        print(f"::warning file=data/registry/pages.yaml::头像缺失：{name} -> {icon}")

    if not missing:
        print("✓ 头像文件齐全")
        return 0
    if strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
