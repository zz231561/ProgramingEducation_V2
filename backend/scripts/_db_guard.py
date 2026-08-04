"""Script 資料庫目標防護 — 避免本機批次工具誤寫生產庫。

背景：所有 script 都透過 `core.database` 讀 `settings.DATABASE_URL`。對生產庫做
一次性維護（如 promote）時會在 shell 覆寫該變數，而變數會殘留在同一個終端機——
之後任何 script 都會落在生產庫上。本模組讓每支 script 明確宣告它的目標環境。

用法：
    from scripts._db_guard import require_local_db   # 只准本機
    from scripts._db_guard import confirm_remote_db  # 可遠端但需確認
"""

import os
import re
import sys

from core.config import settings

_LOCAL_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "host.docker.internal")
# 非互動環境（CI / 管線）用它跳過確認，值必須是 "1"
_OVERRIDE_ENV = "ALLOW_PRODUCTION_WRITE"


def _target() -> str:
    """回傳遮蔽密碼後的 DATABASE_URL，供訊息顯示。"""
    return re.sub(r"//([^:]+):[^@]+@", r"//\1:***@", settings.DATABASE_URL)


def is_local_db() -> bool:
    """DATABASE_URL 是否指向本機。"""
    host = settings.DATABASE_URL.split("@")[-1]
    return any(h in host for h in _LOCAL_HOSTS)


def require_local_db(purpose: str) -> None:
    """只允許本機執行；指向遠端一律中止（無覆寫選項）。

    用於會產生假資料或大量改寫的開發工具——這類 script 沒有任何理由對生產庫跑。
    """
    if is_local_db():
        return
    print(
        f"[中止] {purpose} 只能對本機資料庫執行。\n"
        f"  目前 DATABASE_URL：{_target()}\n"
        f"  這通常是先前對生產庫操作時 export 的變數殘留——\n"
        f"  請開新終端機，或執行 unset DATABASE_URL 後重試。",
        file=sys.stderr,
    )
    raise SystemExit(1)


def confirm_remote_db(purpose: str) -> None:
    """允許對遠端執行，但需互動確認（或設 ALLOW_PRODUCTION_WRITE=1）。

    用於生產庫的合法維護操作（如 promote / metadata patch）。
    """
    if is_local_db():
        return
    if os.getenv(_OVERRIDE_ENV) == "1":
        print(f"[警告] {purpose} 正在對遠端資料庫執行（{_OVERRIDE_ENV}=1）：{_target()}")
        return
    print(f"[警告] {purpose} 即將對遠端資料庫執行：{_target()}")
    if input("  確定要繼續嗎？輸入 yes 確認：").strip() != "yes":
        raise SystemExit("[中止] 已取消")
