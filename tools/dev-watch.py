#!/usr/bin/env python3
"""开发模式内容源监听：当译文/源文件变化时自动跑 sync-site，配合 VitePress
dev 服务器实现「改完即热刷新」的闭环。纯标准库，无第三方依赖。

监听目标（项目根目录下）：
  - data/parsed/ja, data/parsed/zh, data/parsed/characters
  - tools/_manual_zh.json            （译文真值，由 inject_translations.py 重建）
  - glossary/terms.yaml              （站点 UI 文案词表）

运行：python tools/dev-watch.py   （由 start-dev.bat 自动拉起，Ctrl+C 退出）
"""
import os
import sys
import time
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WATCH = [
    os.path.join(ROOT, "data", "parsed", "ja"),
    os.path.join(ROOT, "data", "parsed", "zh"),
    os.path.join(ROOT, "data", "parsed", "characters"),
    os.path.join(ROOT, "tools", "_manual_zh.json"),
    os.path.join(ROOT, "glossary", "terms.yaml"),
]

DEBOUNCE = 1.5  # 秒，避免大批量写入时频繁触发


def snapshot():
    """记录所有监听目标的 mtime（目录则递归所有文件）。"""
    snap = {}
    for p in WATCH:
        if os.path.isdir(p):
            for dp, _, fns in os.walk(p):
                for fn in fns:
                    fp = os.path.join(dp, fn)
                    try:
                        snap[fp] = os.path.getmtime(fp)
                    except OSError:
                        pass
        elif os.path.exists(p):
            try:
                snap[p] = os.path.getmtime(p)
            except OSError:
                pass
    return snap


def sync():
    print("[dev-watch] content changed -> running sync-site ...", flush=True)
    try:
        subprocess.run(
            [sys.executable, "-m", "escah_pipeline.cli", "sync-site"],
            cwd=ROOT,
            check=True,
        )
        print("[dev-watch] sync-site done.", flush=True)
    except subprocess.CalledProcessError as e:
        print("[dev-watch] sync-site failed (exit %d). See output above." % e.returncode, flush=True)


def main():
    prev = snapshot()
    print("[dev-watch] watching content sources (Ctrl+C to stop) ...", flush=True)
    try:
        while True:
            time.sleep(1)
            cur = snapshot()
            if cur == prev:
                continue
            # 文件可能还在写入，防抖后再确认一次
            time.sleep(DEBOUNCE)
            cur2 = snapshot()
            if cur2 != cur:
                prev = cur2
                continue
            try:
                sync()
            except Exception as e:  # noqa: BLE001
                print("[dev-watch] unexpected error:", e, flush=True)
            prev = snapshot()
    except KeyboardInterrupt:
        print("\n[dev-watch] stopped.", flush=True)


if __name__ == "__main__":
    main()
