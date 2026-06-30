from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_URL_DIRECT: str | None = None
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    REDIS_URL: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None
    GOOGLE_CALENDAR_ENABLED: bool = True
    LLM_BASE_URL: str = "http://localhost:8080/v1"
    LLM_MODEL: str = "gemma-4-E2B"
    LLM_TIMEOUT: float = 30.0
    LLM_ENABLED: bool = False
    LLM_TEMPERATURE: float = 0.1
    TELEGRAM_BOT_TOKEN: str | None = None
    BOT_SESSION_TTL: int = 1800

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
