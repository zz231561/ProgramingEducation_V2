"""編譯服務 — g++ + PCH 加速 + 雜湊快取。

流程：cache 命中直接回；未命中→ 沙箱內編譯 → 成功入 cache。
PCH：若 {pch_header}.gch 存在（Dockerfile 產出）則以 -include 掛上，
標準庫標頭解析成本 ~0.25s → ~0.09s（本機實測）；不存在自動跳過（macOS 測試）。
"""

import os
import tempfile
from dataclasses import dataclass

from . import sandbox
from .cache import binary_cache
from .config import settings
from .proc import run_process


@dataclass
class CompileResult:
    binary_path: str | None  # None = 編譯失敗
    compile_output: str
    cache_hit: bool
    timed_out: bool


def _compile_argv(source_name: str, output_name: str) -> list[str]:
    argv = [settings.cxx, *settings.cxx_flags]
    if os.path.exists(settings.pch_header + ".gch"):
        argv += ["-include", settings.pch_header]
    argv += [source_name, "-o", output_name]
    return argv


async def compile_code(code: str) -> CompileResult:
    """編譯 code，回傳可執行檔路徑（快取共享，呼叫端勿刪）。"""
    key = binary_cache.key_for(code)
    cached = binary_cache.get(key)
    if cached is not None:
        return CompileResult(cached, "", cache_hit=True, timed_out=False)

    workdir = tempfile.mkdtemp(prefix="compile-")
    src = os.path.join(workdir, "main.cpp")
    with open(src, "w", encoding="utf-8") as f:
        f.write(code)

    # 沙箱模式下 workdir 綁定為 /box，argv 內用相對檔名
    argv = sandbox.wrap(
        _compile_argv("main.cpp", "app"),
        workdir,
        wall_seconds=settings.compile_wall_seconds,
        cpu_seconds=settings.compile_wall_seconds,
        ram_mb=settings.compile_ram_mb,
    )
    result = await run_process(
        argv,
        cwd=workdir,
        wall_seconds=settings.compile_wall_seconds + 2,
        cpu_seconds=settings.compile_wall_seconds,
        ram_mb=settings.compile_ram_mb,
    )

    binary = os.path.join(workdir, "app")
    if result.timed_out or result.returncode != 0 or not os.path.exists(binary):
        return CompileResult(
            None,
            result.stderr or result.stdout or "compile failed",
            cache_hit=False,
            timed_out=result.timed_out,
        )
    return CompileResult(
        binary_cache.put(key, binary), "", cache_hit=False, timed_out=False
    )
