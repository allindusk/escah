#!/usr/bin/env python3
"""等端口就绪后再打开浏览器（供 start-dev.bat / start-site.bat 调用）。

为什么需要它（2026-09-27）：
  原先两个启动脚本都是「**先开浏览器、后起服务**」：
    · start-site.bat 第 26 行开浏览器、第 27 行才执行 `node build.mjs preview`
      —— 而 preview 是**前台阻塞**，浏览器几乎必然先看到"无法访问" ✗；
    · start-dev.bat 同理（dev 首次启动也要几秒）。
  本脚本轮询目标端口，**就绪后**才打开 URL；超时则明确提示不打开（不再是静默失败）。

用法：
  python tools/open-when-ready.py 4173 http://localhost:4173/escah/
  python tools/open-when-ready.py 5173 http://localhost:5173/escah/ --timeout 120
"""

from __future__ import annotations

import socket
import sys
import time
import webbrowser

DEFAULT_TIMEOUT = 90.0


def port_ready(port: int, timeout: float) -> bool:
    """轮询 127.0.0.1:<port>，就绪返回 True。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.5)
    return False


def main() -> int:
    argv = sys.argv[1:]
    timeout = DEFAULT_TIMEOUT
    if "--timeout" in argv:
        i = argv.index("--timeout")
        try:
            timeout = float(argv[i + 1])
        except (IndexError, ValueError):
            print("[open-when-ready] --timeout 需要一个秒数", flush=True)
            return 2
        del argv[i:i + 2]
    if len(argv) < 2:
        print("用法: python tools/open-when-ready.py <port> <url> [--timeout 秒]", flush=True)
        return 2

    try:
        port = int(argv[0])
    except ValueError:
        print(f"[open-when-ready] 端口不是数字：{argv[0]}", flush=True)
        return 2
    url = argv[1]

    if port_ready(port, timeout):
        print(f"[open-when-ready] 端口 {port} 已就绪，打开 {url}", flush=True)
        webbrowser.open(url)
        return 0
    print(f"[open-when-ready] 等了 {timeout:.0f} 秒，端口 {port} 仍未就绪，"
          f"未打开浏览器（请查看服务窗口的报错）", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
