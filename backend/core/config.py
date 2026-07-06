"""應用程式設定 — 透過 pydantic-settings 管理環境變數。"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """從 .env 或環境變數讀取設定值。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === 應用程式 ===
    APP_NAME: str = "Codedge API"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # === 資料庫 ===
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/programing_education"

    # === Redis ===
    REDIS_URL: str = "redis://localhost:6379/0"

    # === Auth ===
    NEXTAUTH_SECRET: str = ""
    NEXTAUTH_URL: str = "http://localhost:3000"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # === OpenAI ===
    OPENAI_API_KEY: str = ""
    # 6-M 任務導向模型路由（2026-07-06 定案，roadmap 6-M 選型表）：
    # LLM_MODEL = 預設（對話組 EDF Feedback + 分析組 Evidence / Reflection / Comprehension 評分）
    # 分組變數未設定時一律 fallback LLM_MODEL，行為與單一模型時代相同
    LLM_MODEL: str = "gpt-4o"
    # 生成組：Quiz generate / Hint / Comprehension 出題
    LLM_MODEL_GENERATE: str = ""
    # 審查組：Quiz validate——cascade 強把關端
    LLM_MODEL_VALIDATE: str = ""
    # 內容組：6-2b unit content 批次（教科書本體，品質優先）
    LLM_MODEL_CONTENT: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    @property
    def llm_model_generate(self) -> str:
        return self.LLM_MODEL_GENERATE or self.LLM_MODEL

    @property
    def llm_model_validate(self) -> str:
        return self.LLM_MODEL_VALIDATE or self.LLM_MODEL

    @property
    def llm_model_content(self) -> str:
        return self.LLM_MODEL_CONTENT or self.LLM_MODEL

    # === Judge0 ===
    JUDGE0_API_URL: str = "https://judge0-ce.p.rapidapi.com"
    JUDGE0_API_KEY: str = ""

    # === Rate Limiting ===
    RATE_LIMIT_PER_MINUTE: int = 10

    # === 開發者模式 ===
    # 總開關（生產環境保持 False，即使 email 在白名單也無效）
    DEV_MODE_ENABLED: bool = False
    # 白名單 email（逗號分隔），只在 DEV_MODE_ENABLED=true 時生效
    DEV_MODE_EMAILS: str = ""

    @property
    def dev_mode_emails(self) -> set[str]:
        """白名單 email 集合（小寫正規化，空字串過濾）。"""
        return {
            e.strip().lower()
            for e in self.DEV_MODE_EMAILS.split(",")
            if e.strip()
        }

    @property
    def cors_origins(self) -> list[str]:
        """CORS 允許的 origins — 僅 NEXTAUTH_URL。

        生產環境 NEXTAUTH_URL 可能因填寫習慣帶尾斜線（如 `https://domain.com/`），
        但 CORSMiddleware 對 origin 嚴格字串比對，會與 browser 送的 `https://domain.com`
        不符 → 一律 rstrip 防呆。
        """
        return [self.NEXTAUTH_URL.rstrip("/")]


settings = Settings()
