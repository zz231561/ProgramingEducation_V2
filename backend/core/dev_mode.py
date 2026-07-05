"""開發者模式 gating — 總開關 + email 白名單。

安全設計（2026-07-05 使用者定案）：
- 防線在後端：前端 UI 只是入口，所有 dev 端點必須逐一驗證
- 雙重保險：`DEV_MODE_ENABLED` 總開關（生產預設關）+ `DEV_MODE_EMAILS`
  白名單皆為環境變數，白名單不寫死在程式碼、不進 git
- 放在 core 層：rate limit（core）與 API dependency（api 層）共用，
  維持 core 不反向依賴 api 的原則
"""

from core.config import settings


def is_dev_email(email: str | None) -> bool:
    """email 是否為生效中的開發者帳號（開關關閉時一律 False）。"""
    if not settings.DEV_MODE_ENABLED or not email:
        return False
    return email.strip().lower() in settings.dev_mode_emails
