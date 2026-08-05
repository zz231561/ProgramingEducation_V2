"""沙箱指令包裝 — 把「要執行的 argv」轉成「隔離環境下的 argv」。

兩種模式（settings.sandbox）：
- ``nsjail``：生產模式。namespace + cgroup v2 + rlimit 全隔離；學生程式
  無網路（nsjail 預設新 netns）、唯讀系統目錄、非特權 uid。
  旗標值在 R5 於 B 機實測時微調，集中於此檔即可。
- ``none``：本機開發/測試模式。不隔離，僅由 executor 以 setrlimit 限資源。

編譯與執行共用包裝，只差資源參數（編譯需較大 RAM 與可寫 workdir）。
"""

from .config import settings

# nsjail 共通旗標：唯讀掛載系統目錄、非特權 uid、隔離 netns（預設行為）
_NSJAIL_BASE = (
    "nsjail",
    "--really_quiet",
    "-Mo",  # 單次執行模式
    "--user", "65534",
    "--group", "65534",
    "--disable_proc",
    "--rlimit_nproc", "64",
    "-R", "/usr",
    "-R", "/lib",
    "-R", "/etc/alternatives",
)


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
        "--time_limit", str(wall_seconds),
        "--rlimit_cpu", str(cpu_seconds),
        "--rlimit_as", str(ram_mb),  # nsjail 單位為 MB
        "--rlimit_fsize", str(max(settings.output_limit_bytes // (1024 * 1024), 1)),
        "-B", f"{workdir}:/box",
        "--cwd", "/box",
        "--env", "PATH=/usr/bin:/bin",
        "--",
        *argv,
    ]
