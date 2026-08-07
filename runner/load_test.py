"""Runner 併發容量壓測；只用標準函式庫，可直接在 B 機執行。"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
import urllib.request
from pathlib import Path


def read_token(env_file: Path | None) -> str:
    """從 runner .env 讀 token，永不輸出其內容。"""
    if env_file is None:
        return ""
    for line in env_file.read_text().splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == "RUNNER_TOKEN":
            return value.strip()
    return ""


def request_json(url: str, token: str, payload: dict | None = None) -> dict:
    """送出 JSON request 並解析 response。"""
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Runner-Token"] = token
    request = urllib.request.Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.loads(response.read())


async def run_one(base_url: str, token: str, seed: str, index: int) -> dict:
    """送一支不命中 binary cache 的最小 C++ 程式。"""
    code = f"// load-test {seed}\n#include <iostream>\nint main(){{std::cout << {index};}}\n"
    started = time.perf_counter()
    try:
        response = await asyncio.to_thread(
            request_json,
            f"{base_url}/run",
            token,
            {"code": code, "stdin": "", "args": ""},
        )
        return {
            "ok": response.get("status_description") == "Accepted" and response.get("stdout") == str(index),
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "queued_ms": response.get("queued_ms", 0),
            "status": response.get("status_description", "missing status"),
        }
    except (OSError, TimeoutError, ValueError) as error:  # 單筆失敗不應中止整批
        return {
            "ok": False,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "queued_ms": 0,
            "status": f"{type(error).__name__}: {error}",
        }


def percentile(values: list[int], ratio: float) -> int:
    """nearest-rank percentile，避免引入統計套件。"""
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * ratio)))
    return ordered[index]


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--requests", type=int, default=30)
    parser.add_argument("--max-total-seconds", type=float, default=10.0)
    parser.add_argument("--seed", default=str(time.time_ns()), help="每輪唯一值，避免 binary cache")
    args = parser.parse_args()
    if args.requests < 1:
        parser.error("--requests 必須大於 0")

    token = read_token(args.env_file)
    before = await asyncio.to_thread(request_json, f"{args.base_url}/healthz", "")
    started = time.perf_counter()
    results = await asyncio.gather(
        *(run_one(args.base_url, token, args.seed, index) for index in range(args.requests))
    )
    total_seconds = time.perf_counter() - started
    after = await asyncio.to_thread(request_json, f"{args.base_url}/healthz", "")

    latencies = [int(result["latency_ms"]) for result in results]
    queued = [int(result["queued_ms"]) for result in results]
    failures = [result for result in results if not result["ok"]]
    summary = {
        "requests": args.requests,
        "successes": args.requests - len(failures),
        "failures": len(failures),
        "total_seconds": round(total_seconds, 3),
        "latency_ms": {"median": round(statistics.median(latencies)), "p95": percentile(latencies, 0.95), "max": max(latencies)},
        "queued_ms": {"median": round(statistics.median(queued)), "p95": percentile(queued, 0.95), "max": max(queued)},
        "health_before": before,
        "health_after": after,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if failures:
        print(json.dumps({"failure_samples": failures[:3]}, ensure_ascii=False, indent=2))
    return 1 if failures or total_seconds > args.max_total_seconds else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
