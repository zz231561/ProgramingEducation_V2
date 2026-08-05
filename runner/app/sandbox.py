"""沙箱指令包裝 — 把「要執行的 argv」轉成「隔離環境下的 argv」。

兩種模式（settings.sandbox）：
- ``nsjail``：生產模式。namespace + rlimit 全隔離；學生程式無網路
  （nsjail 預設新 netns）、系統目錄唯讀、非特權 uid、workdir 綁為 /box。
- ``none``：本機開發/測試模式。不隔離，僅由 executor 以 setrlimit 限資源。

⚠ jail 內是**全新的 mount namespace**，只有這裡顯式綁定的路徑存在。
2026-08-05 實測踩到兩個坑，勿再移除：
1. PCH 目錄未綁 → `fatal error: /opt/pch/std.h: No such file or directory`
2. PATH 未設 → `collect2: fatal error: cannot find 'ld'`
"""

import os

from .config import settings

# 共通旗標：唯讀掛載系統目錄、非特權 uid、隔離 netns（預設行為）
_NSJAIL_BASE = (
    "nsjail",
    "--really_quiet",
    "-Mo",  # 單次執行模式
    "--user", "65534",
    "--group", "65534",
    "--disable_proc",
    "--rlimit_nproc", str(64),
    "-R", "/usr",
    "-R", "/lib",
    "-R", "/etc/alternatives",
    "-R", "/etc/ld.so.cache",
)


def _pch_mount() -> tuple[str, ...]:
    """PCH 目錄唯讀綁入 jail（不存在則跳過，如本機未建 PCH）。"""
    pch_dir = os.path.dirname(settings.pch_header)
    if os.path.exists(settings.pch_header + ".gch"):
        return ("-R", pch_dir)
    return ()


def wrap(
    argv: list[str],
    workdir: str,
    *,
    wall_seconds: int,
    cpu_seconds: int,
    ram_mb: int,
) -> list[str]:
    """把 argv 包進沙箱。workdir 綁定為 /box 並設為 cwd（可寫）。"""
    if settings.sandbox == "none":
        return argv

    return [
        *_NSJAIL_BASE,
        *_pch_mount(),
        "--time_limit", str(wall_seconds),
        "--rlimit_cpu", str(cpu_seconds),
        "--rlimit_as", str(ram_mb),  # nsjail 單位為 MB
        "--rlimit_fsize", str(max(settings.output_limit_bytes // (1024 * 1024), 1)),
        "-B", f"{workdir}:/box",
        "--cwd", "/box",
        "--env", "PATH=/usr/bin:/bin",
        # GCC 需要暫存目錄；jail 內無 /tmp，導到可寫的 /box
        "--env", "TMPDIR=/box",
        "--",
        *argv,
    ]
