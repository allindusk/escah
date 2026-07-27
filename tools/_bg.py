#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_bg.py - 后台重任务的"护栏 + 日志"守护（最高优先级运维纪律）。

为什么需要：
  - 直接跑 python tools/zh_patch.py 这类长跑命令时，harness 会因"耗时"提前返回，
    底层进程却没被杀、继续后台跑；误以为没跑成又触发一次 → 两份并发写同一批文件互相覆盖。
  - 跑的过程中没有任何进度，出了问题是代码 bug 还是卡住全不知道，白白浪费等待时间。

纪律（每次跑后台重任务都必须遵守）：
  1. 启动前检查 tools/_bg.lock：若已有同类任务在跑（进程仍存活），直接拒绝，杜绝并发写冲突。
  2. 所有输出（含子进程 stdout/stderr）落盘到 tools/_logs/<name>_<时间戳>.log，随时可跟进。
  3. 子进程结束在日志写 [DONE]/[FAIL] 并清除锁，便于判断"跑完没 / 是否异常 / 卡在哪"。

用法：
  python tools/_bg.py start <命令...>
      # 例如: python tools/_bg.py start tools/zh_patch.py
      # start 立刻返回，打印 [START] 含 log 路径；真正工作在分离的 _work 子进程跑。
  python tools/_bg.py status          # 查看当前是否有后台任务在跑及日志路径
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
LOG_DIR = TOOLS / "_logs"
LOCK = TOOLS / "_bg.lock"
DETACH = 0x00000008  # DETACHED_PROCESS (Windows)：脱离控制台，会话结束仍存活


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_lock() -> dict | None:
    if not LOCK.is_file():
        return None
    try:
        lines = LOCK.read_text(encoding="utf-8").strip().splitlines()
        pid = int(lines[0])
        cmd = lines[1] if len(lines) > 1 else "?"
        log = lines[2] if len(lines) > 2 else "?"
        return {"pid": pid, "cmd": cmd, "log": log, "alive": _alive(pid)}
    except Exception:
        return None


def _append_log(log_path: str, s: str) -> None:
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(s + "\n")
    except Exception:
        pass


def cmd_start(argv: list[str]) -> int:
    if not argv:
        print("用法: python tools/_bg.py start <命令...>")
        return 2
    LOG_DIR.mkdir(exist_ok=True)
    exist = _read_lock()
    if exist and exist["alive"]:
        print(
            f"[ABORT] 已有后台任务在运行 pid={exist['pid']} cmd={exist['cmd']}\n"
            f"        日志: {exist['log']}\n"
            f"        请等它结束，或先结束该进程再跑，避免并发写冲突。"
        )
        return 3
    if LOCK.is_file():
        LOCK.unlink()  # 清掉上次的僵尸锁

    name = argv[0].replace(".py", "").replace("/", "_").replace("\\", "_")
    ts = time.strftime("%Y%m%d_%H%M%S")
    log = LOG_DIR / f"{name}_{ts}.log"

    work_args = [sys.executable, str(TOOLS / "_bg.py"), "_work", *argv]
    with open(log, "w", encoding="utf-8") as f:
        f.write(f"[START] {time.strftime('%Y-%m-%d %H:%M:%S')} cmd={' '.join(argv)}\n")
        f.flush()
        proc = subprocess.Popen(
            work_args, stdout=f, stderr=subprocess.STDOUT, creationflags=DETACH
        )
    LOCK.write_text(
        f"{proc.pid}\n{' '.join(argv)}\n{str(log)}\n", encoding="utf-8"
    )
    print(f"[START] pid={proc.pid} log={log}")
    return 0


def cmd_work(argv: list[str]) -> int:
    log_path = None
    info = _read_lock()
    if info:
        log_path = info["log"]

    rc = 1
    try:
        if log_path:
            # 显式把日志文件作为子进程 stdout/stderr，避免 DETACHED 下句柄继承不可靠导致丢失输出
            with open(log_path, "a", encoding="utf-8") as f:
                rc = subprocess.call(
                    [sys.executable, *argv], stdout=f, stderr=subprocess.STDOUT
                )
                f.write(
                    f"[DONE] {time.strftime('%Y-%m-%d %H:%M:%S')} 退出码={rc}\n"
                )
        else:
            rc = subprocess.call([sys.executable, *argv])
    except Exception as e:  # noqa: BLE001
        _append_log(log_path, f"[FAIL] {time.strftime('%Y-%m-%d %H:%M:%S')} {e}")
        rc = 1
    finally:
        if LOCK.is_file():
            LOCK.unlink()
    return rc


def cmd_status() -> int:
    info = _read_lock()
    if info and info["alive"]:
        print(f"[RUNNING] pid={info['pid']} cmd={info['cmd']}\n        日志: {info['log']}")
        return 0
    if info:
        print(f"[STALE] 发现僵尸锁 pid={info['pid']}（进程已不在），已清理。")
        LOCK.unlink()
        return 0
    print("[IDLE] 当前没有后台任务。")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python tools/_bg.py start <命令...> | status")
        return 2
    sub = sys.argv[1]
    if sub == "start":
        return cmd_start(sys.argv[2:])
    if sub == "_work":
        return cmd_work(sys.argv[2:])
    if sub == "status":
        return cmd_status()
    print(f"未知子命令: {sub}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
