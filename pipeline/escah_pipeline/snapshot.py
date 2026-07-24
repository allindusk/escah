"""快照写入与 manifest 维护：sha256 变更检测、断点续抓。"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from . import config


def page_filename(name: str) -> str:
    """页面名 → 安全的快照文件名（URL 编码，规避 Windows 日文文件名与路径长度风险）。"""
    return quote(name, safe="") + ".html"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_snapshot(name: str, content: bytes) -> Path:
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RAW_DIR / page_filename(name)
    path.write_bytes(content)
    return path


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Manifest:
    """data/manifest.json：记录每页 URL、抓取时间、sha256、Last-Modified、状态。"""

    def __init__(self) -> None:
        self.path = config.MANIFEST_FILE
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self.data = {"pages": {}, "assets": {}, "last_update_run": None}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def page(self, name: str) -> dict | None:
        return self.data["pages"].get(name)

    def record_page(
        self,
        name: str,
        url: str,
        content: bytes,
        status: str = "ok",
        error: str | None = None,
        http_last_modified: str | None = None,
        wiki_last_modified: str | None = None,
    ) -> dict:
        entry = {
            "name": name,
            "url": url,
            "file": f"raw/{page_filename(name)}",
            "sha256": sha256_bytes(content),
            "http_last_modified": http_last_modified,
            "wiki_last_modified": wiki_last_modified,
            "fetched_at": utcnow_iso(),
            "status": status,
        }
        if error:
            entry["error"] = error
        self.data["pages"][name] = entry
        return entry

    def record_asset(self, url: str, digest: str, filename: str) -> None:
        self.data["assets"][url] = {
            "sha256": digest,
            "file": f"assets/img/{filename}",
            "fetched_at": utcnow_iso(),
        }
