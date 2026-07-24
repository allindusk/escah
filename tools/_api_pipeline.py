#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM API 自动翻译管线 — 段落级导出 -> 批量翻译(多线程+三模型并发) -> 注入(延后)

用法：
  python tools/_api_pipeline.py                    # 翻译（默认 workers=6）
  python tools/_api_pipeline.py translate 6        # 翻译，6 线程
  python tools/_api_pipeline.py inject             # 仅注入已有结果

关键设计（2026-07-24/25）：
- 译文按模型返回的 [N] 序号对位（旧版按行序 append 导致 001 批错位污染事故）
- 结果文件保留全局序号 [N]（有空洞不重编号），注入端按序号配对
- 每模型限速器（tokenhub RPM=60/模型 → 每模型请求间隔 >=1.1s），429 退避重试不算模型故障
- 子批 partial checkpoint + 不完整 result 自动续补，中断/限流不丢进度
"""
from __future__ import annotations

import io
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from openai import OpenAI, RateLimitError

# 强制 UTF-8 输出（避免 GBK 编码问题导致 print 静默崩溃）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

LOG_FILE = ROOT / "tools" / "_api_pipeline_run.log"
log_fh = open(LOG_FILE, "w", encoding="utf-8", buffering=1)
log_lock = threading.Lock()


def log(msg: str):
    with log_lock:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        log_fh.write(line + "\n")
        log_fh.flush()
        try:
            print(line)
        except Exception:
            pass


# ====== API 配置 ======
BASE_URL = "https://tokenhub.tencentmaas.com/v1"
API_KEY = "sk-G0x4kZk3tHlmXzQelMxy5N2WJ2mTOqMnR6oOfFHzQ0stkShz"
# GLM5 额度已耗尽，本运行只用 5.1 与 5.2（各剩 ~50 万）
MODELS = ["glm-5.1", "glm-5.2"]
MAX_INPUT_TOKENS_PER_CALL = 1500
MAX_OUTPUT_TOKENS = 6000
MAX_SEGMENTS_PER_SUB = 150  # 段数硬上限：防止极短片段(数字等)塞满一子批导致输出被 max_tokens 截断丢尾
TEMP = 0.1
WORKERS = int(os.environ.get("API_WORKERS", "6"))
MODEL_MIN_INTERVAL = 1.1  # RPM 60/模型 → 每模型请求最小间隔秒数

SYSTEM_PROMPT = """你是一个游戏Wiki翻译助手。将日文翻译为简体中文。

规则：
1. 数字、英文缩写（SSR/SR/R/CV/NPC等）保持不变。
2. 专用名：角色名、技能名、装备名保留日文不翻译。
3. 与中文不冲突的汉字词可直接沿用。
4. 术语统一：キャラ→角色、スタミナ→体力、ガチャ→扭蛋、レイド→讨伐战、バフ→增益、デバフ→减益、必殺技→必杀技、固有効果→固有效果、限界突破→界限突破、覚醒→觉醒。
5. 语气简洁准确，与游戏Wiki一致。
6. 输出必须保留每行行首的 [N] 序号，与输入的序号一一对应；不得合并、拆分、跳过或新增行。
7. 即使某行无需翻译（如纯数字、与中文写法相同），也必须原样输出该行 [N] 原文，不得省略任何一行。

输出格式：只输出译文行（形如 [N] 译文），别无其他。"""

# ====== 线程安全全局状态 ======
state_lock = threading.Lock()
# 各模型剩余额度上限（估算值，达到即停止该模型，避免超额）
token_budget = {m: 500_000 for m in MODELS}
total_used = {m: 0 for m in MODELS}
model_health = {m: True for m in MODELS}
model_cooldown = {m: 0.0 for m in MODELS}
model_dead = {m: False for m in MODELS}  # 额度耗尽等永久性故障：本运行内不再启用
_rr_counter = [0]


def is_quota_error(e: Exception) -> bool:
    """识别额度/配额耗尽类错误（与限流 429 区分，后者可重试）。"""
    code = getattr(e, "code", None)
    s = f"{type(e).__name__} {code} {str(e)}".lower()
    keys = ["insufficient_quota", "quota", "额度", "余额", "balance",
            "insufficient", "account", "limit reached", "out of", "exceeded"]
    return any(k in s for k in keys)


class ModelLimiter:
    """每模型请求限速：串行发放时间槽，保证同模型两次请求间隔 >= min_interval。"""

    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self.locks = {m: threading.Lock() for m in MODELS}
        self.next_ok = {m: 0.0 for m in MODELS}

    def acquire(self, m: str):
        with self.locks[m]:
            now = time.time()
            slot = max(now, self.next_ok[m])
            self.next_ok[m] = slot + self.min_interval
        delay = slot - time.time()
        if delay > 0:
            time.sleep(delay)


limiter = ModelLimiter(MODEL_MIN_INTERVAL)


def estimate_tokens(text: str) -> int:
    cjk = sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u30ff' or '\u3000' <= c <= '\u303f')
    ascii_chars = len(text) - cjk
    return int(cjk / 1.5 + ascii_chars / 4 + 1)


def pick_model() -> str | None:
    """轮询选一个健康且余额充足的模型（三模型并发分流）。永久停用的模型不再入选。"""
    with state_lock:
        t = time.time()
        for m in MODELS:
            if (not model_health[m]) and (not model_dead[m]) and t >= model_cooldown[m]:
                model_health[m] = True
        avail = [m for m in MODELS if model_health[m] and (not model_dead[m]) and token_budget.get(m, 0) > 0]
        if not avail:
            # 全部临时故障时，放行非永久停用的模型再试一次
            avail = [m for m in MODELS if (not model_dead[m]) and token_budget.get(m, 0) > 0]
            for m in avail:
                model_health[m] = True
        if not avail:
            return None
        m = avail[_rr_counter[0] % len(avail)]
        _rr_counter[0] += 1
        return m


def mark_fail(m: str):
    with state_lock:
        model_health[m] = False
        model_cooldown[m] = time.time() + 300  # 停用 5 分钟


def mark_dead(m: str):
    """永久停用（额度耗尽等）：本运行内不再被轮询选中。"""
    with state_lock:
        model_health[m] = False
        model_dead[m] = True
        model_cooldown[m] = float("inf")


def mark_ok(m: str):
    with state_lock:
        model_health[m] = True


def deduct_tokens(model: str, tokens: int):
    with state_lock:
        if model in token_budget:
            token_budget[model] -= tokens
            total_used[model] += tokens


def run_step(script, *args: str) -> bool:
    cmd = [sys.executable, str(script)] + list(args)
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def extract_segments(batch_text: str) -> list[str]:
    segs = []
    for line in batch_text.split("\n"):
        m = re.match(r"^\[\d+\]\s+(.+)$", line)
        if m:
            segs.append(m.group(1).strip())
    return segs


def load_result_map(result_path: Path) -> dict[int, str]:
    """读取 result/partial 文件为 {0基全局索引: 译文}。"""
    out: dict[int, str] = {}
    if not result_path.exists():
        return out
    text = result_path.read_text(encoding="utf-8")
    if result_path.suffix == ".json" and text.lstrip().startswith("{"):
        try:
            return {int(k): v for k, v in json.loads(text).items()}
        except Exception:
            return out
    for line in text.split("\n"):
        m = re.match(r"^\[(\d+)\]\s+(.+)$", line)
        if m:
            out[int(m.group(1)) - 1] = m.group(2).strip()
    return out


def split_into_sub_batches(segments: list[str]) -> list[tuple[int, list[str]]]:
    """按 token 预算拆分子批，返回 (全局起始索引, 段列表)。"""
    sub_batches: list[tuple[int, list[str]]] = []
    current: list[str] = []
    current_tokens = 0
    start = 0
    budget = MAX_INPUT_TOKENS_PER_CALL - estimate_tokens(SYSTEM_PROMPT)

    for idx, text in enumerate(segments):
        t = estimate_tokens(text)
        if current and (current_tokens + t > budget or len(current) >= MAX_SEGMENTS_PER_SUB):
            sub_batches.append((start, current))
            current = []
            current_tokens = 0
            start = idx
        current.append(text)
        current_tokens += t

    if current:
        sub_batches.append((start, current))
    return sub_batches


def translate_segments(sub_batch: list[str], model: str, client: OpenAI):
    """翻译一个子批。返回 (status, {子批内0基索引: 译文})，status ∈ ok/rate/fail。"""
    lines = [f"[{i+1}] {text}" for i, text in enumerate(sub_batch)]
    user_text = "\n".join(lines)

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            temperature=TEMP,
            max_tokens=MAX_OUTPUT_TOKENS,
            extra_body={"thinking": {"type": "disabled"}},
            timeout=90,
        )
        content = resp.choices[0].message.content or ""

        u = getattr(resp, "usage", None)
        in_tok = (u.prompt_tokens if u and u.prompt_tokens else estimate_tokens(user_text) + estimate_tokens(SYSTEM_PROMPT))
        out_tok = (u.completion_tokens if u and u.completion_tokens else estimate_tokens(content))
        deduct_tokens(model, in_tok + out_tok)

        # ★ 按 [N] 序号对位（模型漏行/乱序不会错位）
        result: dict[int, str] = {}
        for line in content.strip().split("\n"):
            m = re.match(r"^\[(\d+)\]\s*(.+)$", line.strip())
            if m:
                n = int(m.group(1))
                if 1 <= n <= len(sub_batch):
                    zh = m.group(2).strip()
                    if zh:
                        result[n - 1] = zh
        return ("ok", result) if result else ("fail", None)

    except RateLimitError:
        return ("rate", None)
    except Exception as e:
        if is_quota_error(e):
            return ("quota", None)
        log(f"  API 出错 ({model}): {type(e).__name__}: {str(e)[:100]}")
        return ("fail", None)


def translate_batch(batch_path: Path, output_dir: Path, client: OpenAI, workers: int) -> bool:
    """多线程翻译一个 batch，429 退避重试，partial checkpoint 断点续跑。"""
    segments = extract_segments(batch_path.read_text(encoding="utf-8"))
    if not segments:
        return True

    sub_batches = split_into_sub_batches(segments)
    result_path = output_dir / f"{batch_path.stem}_result.json"
    partial_path = output_dir / f"{batch_path.stem}_partial.json"

    # 断点续跑：合并已有 result（可能不完整）与 partial
    all_zh: dict[int, str] = {}
    all_zh.update(load_result_map(result_path))
    all_zh.update(load_result_map(partial_path))
    if all_zh:
        log(f"  续跑: 已有 {len(all_zh)} 条")

    done_lock = threading.Lock()
    done_count = [0]
    t_start = time.time()
    rate_hits = [0]

    def work(job):
        start_idx, sub = job
        if all(start_idx + k in all_zh for k in range(len(sub))):
            return 0
        zh_map = None
        for attempt in range(6):
            model = pick_model()
            if model is None:
                return -1
            limiter.acquire(model)
            status, zh_map = translate_segments(sub, model, client)
            if status == "ok":
                mark_ok(model)
                break
            if status == "rate":
                with done_lock:
                    rate_hits[0] += 1
                time.sleep(1.5 * (attempt + 1) + random.random())  # 429: 退避重试，不标故障
                continue
            if status == "quota":
                log(f"  ⚠️ {model} 额度耗尽，永久移出轮询（剩余 {(', '.join(m for m in MODELS if model_health[m] and not model_dead[m])) or '无'}）")
                mark_dead(model)
                time.sleep(0.2)  # 下一轮 attempt 选其他模型，不再对该模型重试
                continue
            mark_fail(model)  # 超时/其他错误：临时停用该模型
        if not zh_map:
            return 0
        with done_lock:
            for k, zh in zh_map.items():
                all_zh[start_idx + k] = zh
            done_count[0] += 1
            n_done = done_count[0]
            if n_done % 5 == 0:
                partial_path.write_text(
                    json.dumps({str(k): v for k, v in all_zh.items()}, ensure_ascii=False),
                    encoding="utf-8")
                elapsed = time.time() - t_start
                rate = len(all_zh) / elapsed * 60 if elapsed > 0 else 0
                log(f"  进度 {n_done} 子批 | 已译 {len(all_zh)}/{len(segments)} 段 | {rate:.0f} 段/分 | 429×{rate_hits[0]}")
        return len(zh_map)

    log(f"{batch_path.name}: {len(segments)} 段 -> {len(sub_batches)} 子批, workers={workers}")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(work, job) for job in sub_batches]
        for f in as_completed(futures):
            f.result()

    if all_zh:
        # 兜底填充：未译出的段用原文（数字/无需翻译者即正确译文；其余保留日文不破坏对齐与序号）
        for i, seg in enumerate(segments):
            all_zh.setdefault(i, seg)
        lines = [f"[{i+1}] {all_zh[i]}" for i in sorted(all_zh)]
        result_path.write_text("\n".join(lines), encoding="utf-8")
        if partial_path.exists():
            partial_path.unlink()
        miss = sum(1 for i in range(len(segments)) if all_zh[i] == segments[i])
        log(f"  保存 {len(all_zh)} 条译文 (其中 {miss} 条原文兜底) -> {result_path.name}")
        return True
    return False


def inject_translations(batch_path: Path, result_path: Path):
    """按 [N] 全局序号配对并注入（zh 行的 N 直接对应 ja_list[N-1]）。"""
    ja_list = extract_segments(batch_path.read_text(encoding="utf-8"))
    result_text = result_path.read_text(encoding="utf-8")

    pairs = []
    for line in result_text.split("\n"):
        m = re.match(r"^\[(\d+)\]\s+(.+)$", line)
        if m:
            n = int(m.group(1))
            zh = m.group(2).strip()
            if 1 <= n <= len(ja_list) and zh:
                ja = ja_list[n - 1]
                if zh != ja:
                    pairs.append([ja, zh])

    if not pairs:
        log("  无有效翻译对")
        return

    json_path = result_path.parent / f"{result_path.stem}_pairs.json"
    json_path.write_text(json.dumps(pairs, ensure_ascii=False, indent=2), encoding="utf-8")

    log(f"  注入 {len(pairs)} 对 -> zh_patch.py")
    run_step(ROOT / "tools" / "_inject_batch.py", str(json_path), batch_path.stem)


# ====== 主入口 ======

def main(workers: int):
    log("超昂大战 WIKI 翻译管线 (GLM 三模型并发+限速版)")
    log(f"模型: {', '.join(MODELS)} | workers={workers} | 每模型间隔 {MODEL_MIN_INTERVAL}s | 每调用 ~{MAX_INPUT_TOKENS_PER_CALL} tok")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL, max_retries=0)

    batch_dir = ROOT / "tools" / "_api_batches"
    batches = sorted(batch_dir.glob("*.txt"))
    if not batches:
        log("错误：请先运行 python tools/_export_for_api.py && python tools/_split_for_api.py")
        return

    results_dir = ROOT / "tools" / "_api_results"
    results_dir.mkdir(parents=True, exist_ok=True)

    def have_count(bp: Path) -> tuple[int, int]:
        n_seg = len(extract_segments(bp.read_text(encoding="utf-8")))
        n_have = len(load_result_map(results_dir / f"{bp.stem}_result.json"))
        return n_have, n_seg

    # 多轮：第一轮跑全部，后续轮次回头补模型漏行的批；无增量则停
    for round_i in range(1, 4):
        total_before = sum(have_count(bp)[0] for bp in batches)
        pending = [bp for bp in batches if (lambda h: h[0] < h[1] * 0.995)(have_count(bp))]
        if not pending:
            log("全部批次已完整。")
            break
        log(f"--- 第 {round_i} 轮: 待处理 {len(pending)} 批 ---")
        if all(model_dead[m] for m in MODELS):
            log("⚠️ 全部模型额度耗尽或故障，无法继续。请补充额度或调整 MODELS 后重跑。")
            break
        for batch_path in pending:
            n_have, n_seg = have_count(batch_path)
            if n_have:
                log(f"续补 {batch_path.name} (现有 {n_have}/{n_seg})")
            translate_batch(batch_path, results_dir, client, workers)
        total_after = sum(have_count(bp)[0] for bp in batches)
        log(f"第 {round_i} 轮结束: {total_before} -> {total_after} (+{total_after - total_before})")
        if total_after <= total_before:
            log("本轮无增量（剩余为顽固漏行），停止。")
            break

    log("--- Token 消耗报告 ---")
    for m in MODELS:
        flag = " [已停机]" if model_dead[m] else (" [临时停用]" if not model_health[m] else "")
        log(f"  {m}: 已用 {total_used[m]:,}{flag}")
    if any(model_dead[m] for m in MODELS):
        log(f"⚠️ 已永久停用: {', '.join(m for m in MODELS if model_dead[m])}。剩余可用: {', '.join(m for m in MODELS if not model_dead[m]) or '无'}")

    log("=== 翻译完成（仅生成译文，未注入/未应用）===")
    log("稍后统一注入：python tools/_api_pipeline.py inject")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "inject":
        results_dir = ROOT / "tools" / "_api_results"
        batch_dir = ROOT / "tools" / "_api_batches"
        for rf in sorted(results_dir.glob("*_result.json")):
            bf = batch_dir / f"{rf.stem.replace('_result','')}.txt"
            if bf.exists():
                log(f"{bf.name}:")
                inject_translations(bf, rf)
        log("注入完成")
    else:
        w = WORKERS
        for a in sys.argv[1:]:
            if a.isdigit():
                w = int(a)
        main(w)
