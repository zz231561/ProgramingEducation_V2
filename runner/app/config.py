"""Runner 設定 — 全部來自環境變數，數值預設對齊 docs/server-plan.md 參數表。

設計意圖：模組層級單例 `settings`，呼叫端以屬性存取（不解構），
讓測試能以 monkeypatch 覆寫單一參數而不需重建 app。
"""

import os
import tempfile
from dataclasses import dataclass, field


def _int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


@dataclass
class Settings:
    # 認證：空字串 = 不驗（僅限本機開發/測試）；生產 compose 必須設定
    token: str = field(default_factory=lambda: os.environ.get("RUNNER_TOKEN", ""))

    # 沙箱模式：nsjail（生產）/ none（本機測試，僅 rlimit）
    sandbox: str = field(default_factory=lambda: os.environ.get("RUNNER_SANDBOX", "nsjail"))

    # 編譯器
    cxx: str = field(default_factory=lambda: os.environ.get("RUNNER_CXX", "g++"))
    cxx_flags: tuple[str, ...] = ("-std=c++17", "-O0", "-Wall")
    # PCH：預編譯標準庫標頭（Dockerfile 產出 std.h + std.h.gch）；不存在則自動跳過
    pch_header: str = field(
        default_factory=lambda: os.environ.get("RUNNER_PCH_HEADER", "/opt/pch/std.h")
    )

    # 資源上限（server-plan.md 定案值）
    compile_wall_seconds: int = field(default_factory=lambda: _int("RUNNER_COMPILE_WALL", 10))
    compile_ram_mb: int = field(default_factory=lambda: _int("RUNNER_COMPILE_RAM_MB", 512))
    exec_wall_seconds: int = field(default_factory=lambda: _int("RUNNER_EXEC_WALL", 10))
    exec_cpu_seconds: int = field(default_factory=lambda: _int("RUNNER_EXEC_CPU", 5))
    exec_ram_mb: int = field(default_factory=lambda: _int("RUNNER_EXEC_RAM_MB", 256))
    exec_pids: int = field(default_factory=lambda: _int("RUNNER_EXEC_PIDS", 64))
    output_limit_bytes: int = field(
        default_factory=lambda: _int("RUNNER_OUTPUT_LIMIT", 8 * 1024 * 1024)
    )

    # 並行編譯閘（2C2G 安全值）與排隊上限
    gate_slots: int = field(default_factory=lambda: _int("RUNNER_GATE_SLOTS", 2))
    gate_queue_timeout: int = field(default_factory=lambda: _int("RUNNER_QUEUE_TIMEOUT", 30))

    # 編譯結果快取
    cache_dir: str = field(
        default_factory=lambda: os.environ.get(
            "RUNNER_CACHE_DIR", os.path.join(tempfile.gettempdir(), "runner-cache")
        )
    )
    cache_max_entries: int = field(default_factory=lambda: _int("RUNNER_CACHE_MAX", 256))

    # 程式碼長度上限（防濫用；教學程式遠低於此）
    max_code_bytes: int = field(default_factory=lambda: _int("RUNNER_MAX_CODE", 100_000))


settings = Settings()
