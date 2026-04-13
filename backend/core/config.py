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
    APP_NAME: str = "ProgramingEducation API"
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
    LLM_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # === Judge0 ===
    JUDGE0_API_URL: str = "https://judge0-ce.p.rapidapi.com"
    JUDGE0_API_KEY: str = ""

    # === Rate Limiting ===
    RATE_LIMIT_PER_MINUTE: int = 10

    @property
    def cors_origins(self) -> list[str]:
        """CORS 允許的 origins — 僅 NEXTAUTH_URL。"""
        return [self.NEXTAUTH_URL]


settings = Settings()
