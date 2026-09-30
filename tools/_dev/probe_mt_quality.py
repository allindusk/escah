# -*- coding: utf-8 -*-
"""质量归因探针：把「库里现存的坏译」与「**现在重跑同一个引擎**的结果」并排对照。

要回答的问题（2026-09-27 用户提出）：
  ① 之前的译文为什么那么差——是谷歌翻译本身只能到那个水平，还是流水线的用法有问题？
  ② 能不能验证翻译质量？

做法：对每条测试文本，并排打印
    · ja（真值原文）
    · 库里现存的 zh（可能是很久以前译的 ✗）
    · **现在**用 `gtrans.translate_text` 重译一遍的结果（同一引擎、同一接口）
若「现译」明显好于「库存」 ⇒ 说明库存坏译未必是引擎当下的水平（可能是旧版流水线/别的机制/片段化遗留）✓
若两者一样差 ⇒ 说明是引擎/用法的固有上限 ✗，据此再决定要不要在 CI 里保留机翻。

用法：python tools/_dev/probe_mt_quality.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline import gtrans  # noqa: E402
from escah_pipeline.i18n import _blocks_of, _keys_of, has_i18n, load_entries  # noqa: E402

BR = "\x01"

# (说明, 待测日文, 该文本所属页（用于取库存译文；None 表示不查）)
CASES = [
    ("技能标题（短标题）", "スタン抵抗ダウン 一覧", "raid-buff-debuff"),
    ("把角色名当地名的典型", "ナルト", "map-list"),
    ("术语：耐力", "スタミナ", "characters/真夏のエスカ・オニキス"),
    ("技能描述（含场地/命中）", "20秒間、自軍フィールドの命中50アップ", "characters/真夏のエスカ・オニキス"),
    ("技能描述（更短片段）", "自軍フィールドの命中50アップ", None),
    ("机制词：掩护", "かばう", "characters/バトラー・ヘプタスロン"),
    ("整句（含掩护）", "かばうが発動しないコンテンツなので回避ダウンしか役割がなく、それならRやSRにもできるキャラは多い。", "characters/バトラー・ヘプタスロン"),
    ("专名：神骑豪泽尔", "神騎ハウゼル", "characters/神騎ハウゼル"),
    ("专名：闪忍荷妮特", "閃忍ホーネット", "characters/閃忍ホーネット"),
    ("专名：艾斯卡蕾雅", "エスカレイヤー", "characters/盛夏のエスカレイヤー"),
    ("专名串（拟声+角色）", "ビートアミュレット・ノノノや制服ニャンコなど", "characters/真夏のエスカ・オニキス"),
    ("装备名", "ハニージッポ", "characters/真夏のエスカ・オニキス"),
    ("整句（长句，攻防数值）", "敵一列に魔法4倍ダメージ", "characters/真夏のキクリ"),
    ("机制整句（必杀能量）", "10秒間、自身の命中50アップ", "characters/真夏のエスカ・オニキス"),
]


def stored_zh(slug: str | None, ja: str) -> str:
    if not slug or not has_i18n(slug):
        return "（未查）"
    en = load_entries(slug)
    for ent in list(_keys_of(en).values()) + list(_blocks_of(en).values()):
        for seg in (ent.get("ja") or "").split(BR):
            if seg.strip() == ja.strip():
                zh = ent.get("zh") or ""
                parts = zh.split(BR)
                if len(parts) == 1:
                    return zh.strip() or "（空）"
                idx = [i for i, s in enumerate((ent.get("ja") or "").split(BR)) if s.strip() == ja.strip()]
                if idx and idx[0] < len(parts):
                    return (parts[idx[0]] or "").strip() or "（空）"
    return "（未找到该原文）"


def main() -> int:
    print("=" * 100)
    print("真实管线路径（先 pre_substitute 术语/专名，再送谷歌）vs 库存译文")
    print("⚠️ 上一版探针直接调 translate_text，绕过了 pre_substitute ✗ → 会把「专名硬译」"
          "误判成谷歌的固有水平（实测：神騎ハウゼル 未替换时→「神圣骑士豪瑟」✗，"
          "替换后应保留「神骑豪泽尔」✓）。")
    print("=" * 100)
    for label, ja, slug in CASES:
        old = stored_zh(slug, ja)
        try:
            pre = gtrans.pre_substitute(ja)
        except Exception as e:  # noqa: BLE001
            pre = f"（预替换失败：{e}）"
        try:
            new = gtrans.translate_text(pre, src="ja", tgt="zh-CN")
        except Exception as e:  # noqa: BLE001
            new = f"（翻译失败：{e}）"
        # ③ 占位符保护路径（拟议新方案：日文保持完整，专名/术语挖成 [[i]]，翻完还原）
        try:
            protected, spans = gtrans.protect_ja(ja)
            raw = gtrans.translate_text(protected, src="ja", tgt="zh-CN")
            prot, missing = gtrans.restore_zh(raw, spans)
            prot_info = f"{prot}   〔占位符 {len(spans)} 个，未还原 {missing} 个〕"
        except Exception as e:  # noqa: BLE001
            protected, prot_info = "（保护失败）", f"（保护失败：{e}）"
        print(f"\n【{label}】")
        print(f"  ja    : {ja}")
        if pre != ja:
            print(f"  旧·预替换: {pre}")
        if protected != ja:
            print(f"  新·占位符: {protected}")
        print(f"  库存  : {old}")
        print(f"  旧路径: {new}")
        print(f"  新路径: {prot_info}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
