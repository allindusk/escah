"""统一日志：控制台 + data/logs 文件，全链路 UTF-8。"""
from __future__ import annotations

import logging
import sys
from datetime import datetime

from . import config

_LOGGER_NAME = "escah"

# Windows 控制台默认 GBK，强制 UTF-8 输出
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def get_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(
        config.LOG_DIR / f"pipeline-{datetime.now():%Y%m%d}.log", encoding="utf-8"
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger
