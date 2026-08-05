"""沙箱指令包裝 — 把「要執行的 argv」轉成「隔離環境下的 argv」。

兩種模式（settings.sandbox）：
- ``nsjail``：生產模式。namespace + rlimit 全隔離；學生程式無網路
  （nsjail 預設新 netns）、系統目錄唯讀、非特權 uid、workdir 綁為 /box。
- ``none``：本機開發/測試模式。不隔離，僅由 executor 以 setrlimit 限資源。

⚠ jail 內是**全新的 mount namespace**，只有這裡顯式綁定的路徑存在。
實測踩過三個坑，勿再精簡：
1. PCH 目錄未綁 → `fatal error: /opt/pch/std.h: No such file or directory`
2. PATH 未設 → `collect2: fatal error: cannot find 'ld'`
3. `/lib64` 未綁（amd64）→ execve 回報 "No such file or directory"（缺的是
   動態載入器，不是執行檔本身；arm64 因 loader 在 /lib 底下而測不出來）
"""

import os

from .config import settings

_NSJAIL_FLAGS = (
    "nsjail",
    "--really_quiet",
    "-Mo",  # 單次執行模式
    "--user", "65534",
    "--group", "65534",
    "--disable_proc",
    "--rlimit_nproc", str(64),
)

# 唯讀掛載的候選路徑；**不存在者自動略過**（nsjail 對不存在的來源會失敗）。
# ⚠ `/lib64` 不可少：amd64 的動態載入器在 `/lib64/ld-linux-x86-64.so.2`，
# 少了它 execve 會回報 "No such file or directory"（看起來像執行檔不見了）。
# arm64 的 loader 在 /lib 底下，故本機 Apple Silicon 測不出這個缺陷
# —— 2026-08-06 在 B 機（amd64）實測才暴露，勿再刪減此清單。
_RO_CANDIDATES = (
    "/usr",
    "/lib",
    "/lib64",
    "/lib32",
    "/etc/alternatives",
    "/etc/ld.so.cache",
    "/etc/ld.so.conf",
    "/etc/ld.so.conf.d",
)


def _ro_mounts() -> list[str]:
    """存在的系統路徑 + PCH 目錄（未建 PCH 時略過，如本機測試）。"""
    paths = [p for p in _RO_CANDIDATES if os.path.exists(p)]
    if os.path.exists(settings.pch_header + ".gch"):
        paths.append(os.path.dirname(settings.pch_header))
    mounts: list[str] = []
    for p in paths:
        mounts += ["-R", p]
    return mounts


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
        *_NSJAIL_FLAGS,
        *_ro_mounts(),
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
