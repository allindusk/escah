# -*- coding: utf-8 -*-
"""密钥读取：环境变量 / 本地 .env 优先，其次解密「入库密文」。

为什么要有这一层（2026-11-13）：
  谷歌翻译接口的 API Key 曾以明文常量写在 `gtrans.py` 里，被 GitHub secret
  scanning 报警。明文一旦进过仓库，就算删掉，历史里仍然查得到 —— 所以
  **真正的修复是去 Google Cloud 轮换/吊销那个 key**，本模块只解决「代码里
  不再出现明文」这件事（避免继续被扫描、避免顺手被抄）。

取值优先级（`get_secret("GOOGLE_API_KEY")`）：
  1. 进程环境变量 `GOOGLE_API_KEY`
  2. 项目根 `.env` 里的 `GOOGLE_API_KEY`（.env 已被 .gitignore 忽略，不入库）
  3. `.env` 里的 `GOOGLE_API_KEY_ENC`（密文）+ `ESCAH_SECRET_KEY`（主口令）→ 解密

密文用 `encrypt_secret()` 生成：
  python -m escah_pipeline.secrets encrypt "sk-xxx"     # 打印 escah1:… 密文
  python -m escah_pipeline.secrets get GOOGLE_API_KEY   # 自检当前能否取到（只打印前 6 位）

⚠️ 安全边界（别误读）：密文与主口令若同时存在于同一个仓库/同一台机器，等同于明文。
   本机制防的是「仓库里被扫描 / 被人顺眼看到」，不是「攻击者已经拿到仓库」。
   对称加密用的是标准库 PBKDF2-HMAC-SHA256 派生 + SHA256 计数器流 + HMAC 校验
   （Encrypt-then-MAC），够用但刻意不引入第三方依赖（CI 不必装 cryptography）。
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import sys
from pathlib import Path

_MAGIC = "escah1"
KDF_ROUNDS = 200_000
_ENV_LOADED = False


# ---------------------------------------------------------------- .env 读取 ----
def _repo_root() -> Path:
    # pipeline/escah_pipeline/secrets.py → 仓库根
    return Path(__file__).resolve().parents[2]


def load_dotenv(force: bool = False) -> None:
    """把项目根 .env 载入 os.environ（不覆盖已存在的变量）。

    优先用 python-dotenv（依赖里已有），没装则退回手写解析（够处理 KEY=VALUE 与引号）。
    """
    global _ENV_LOADED
    if _ENV_LOADED and not force:
        return
    _ENV_LOADED = True
    path = _repo_root() / ".env"
    if not path.is_file():
        return
    try:
        from dotenv import load_dotenv as _load  # type: ignore

        _load(path, override=False)
        return
    except Exception:  # noqa: BLE001 - 没装 dotenv 也不能让取密钥失败
        pass
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if key and key not in os.environ:
            os.environ[key] = val


# ------------------------------------------------------------------ 加解密 ----
def _derive(master: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", master.encode("utf-8"), salt, KDF_ROUNDS)


def _stream(key: bytes, nonce: bytes, size: int) -> bytes:
    """SHA256(key‖nonce‖counter) 串联成密钥流（只用于掩蔽，安全性靠 HMAC 校验）。"""
    out = bytearray()
    counter = 0
    while len(out) < size:
        out += hashlib.sha256(key + nonce + counter.to_bytes(8, "big")).digest()
        counter += 1
    return bytes(out[:size])


def _xor(data: bytes, ks: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(data, ks))


def encrypt_secret(plain: str, master: str) -> str:
    """明文 → `escah1:base64(salt‖nonce‖ciphertext‖tag)`。"""
    if not plain:
        raise ValueError("待加密内容为空")
    if not master:
        raise ValueError("缺少主口令（ESCAH_SECRET_KEY）")
    salt, nonce = os.urandom(16), os.urandom(16)
    key = _derive(master, salt)
    data = plain.encode("utf-8")
    cipher = _xor(data, _stream(key, nonce, len(data)))
    tag = hmac.new(key, b"tag" + nonce + cipher, hashlib.sha256).digest()[:16]
    blob = base64.urlsafe_b64encode(salt + nonce + cipher + tag).decode("ascii")
    return f"{_MAGIC}:{blob}"


def decrypt_secret(token: str, master: str) -> str:
    """`escah1:` 密文 → 明文；主口令不对或密文被改动都会抛 ValueError。"""
    token = (token or "").strip()
    if not token.startswith(_MAGIC + ":"):
        raise ValueError("不是本模块生成的密文（应以 escah1: 开头）")
    raw = base64.urlsafe_b64decode(token[len(_MAGIC) + 1:].encode("ascii"))
    if len(raw) < 16 + 16 + 16:
        raise ValueError("密文长度异常")
    salt, nonce, rest = raw[:16], raw[16:32], raw[32:]
    cipher, tag = rest[:-16], rest[-16:]
    key = _derive(master, salt)
    expect = hmac.new(key, b"tag" + nonce + cipher, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(tag, expect):
        raise ValueError("主口令不正确，或密文已损坏")
    return _xor(cipher, _stream(key, nonce, len(cipher))).decode("utf-8")


# ------------------------------------------------------------------- 取值 ----
def get_secret(name: str, default: str = "") -> str:
    """按 环境变量 → .env → 密文+主口令 的顺序取密钥；都取不到返回 default。"""
    load_dotenv()
    val = os.environ.get(name, "")
    if val:
        return val
    enc = os.environ.get(f"{name}_ENC") or os.environ.get(f"ESCAH_ENC_{name}") or ""
    master = os.environ.get("ESCAH_SECRET_KEY", "")
    if enc and master:
        return decrypt_secret(enc, master)
    return default


def mask(value: str, keep: int = 6) -> str:
    """日志/自检用：只露前几位。"""
    if not value:
        return "(空)"
    return value[:keep] + "…" + f"（{len(value)} 位）"


# --------------------------------------------------------------------- CLI ----
def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(__doc__)
        return 2
    cmd = args[0]

    if cmd == "encrypt":
        if len(args) < 2:
            print("用法：python -m escah_pipeline.secrets encrypt <明文>")
            return 2
        load_dotenv()
        master = os.environ.get("ESCAH_SECRET_KEY", "")
        if not master:
            print("缺少主口令：请先在 .env 设置 ESCAH_SECRET_KEY=<随便一串长期口令>")
            return 1
        print(encrypt_secret(args[1], master))
        return 0

    if cmd == "decrypt":
        if len(args) < 2:
            print("用法：python -m escah_pipeline.secrets decrypt <escah1:…>")
            return 2
        load_dotenv()
        master = os.environ.get("ESCAH_SECRET_KEY", "")
        print(decrypt_secret(args[1], master))
        return 0

    if cmd == "get":
        name = args[1] if len(args) > 1 else "GOOGLE_API_KEY"
        value = get_secret(name)
        source = "环境变量/.env" if os.environ.get(name) else ("密文解密" if value else "未找到")
        print(f"{name}: {mask(value)} ← {source}")
        return 0 if value else 1

    print(f"未知子命令：{cmd}（可用：encrypt / decrypt / get）")
    return 2


if __name__ == "__main__":
    sys.exit(main())
