from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/verity"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "RS256"
    JWT_PRIVATE_KEY_PATH: str = ""
    JWT_PUBLIC_KEY_PATH: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SENTRY_DSN: str = ""
    ENVIRONMENT: str = "development"
    TELEMETRY_ENABLED: bool = False
    CORS_ORIGINS: str = "http://localhost:5173"
    LICENSE_PUBLIC_KEY: str = ""
    LICENSE_FREE_SEATS: int = 5
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_MAX_TOKENS: int = 600
    LLM_PROVIDER: str = "openai"
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "llama3.2"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    AI_SYNTHESIS_ENABLED: bool = True

    VANTA_API_KEY: str = ""
    VANTA_API_BASE: str = "https://api.vanta.com"
    VANTA_INTEGRATION_MODE: str = "mock"

    @property
    def llm_configured(self) -> bool:
        return bool(self.LLM_API_KEY) or self.LLM_PROVIDER == "ollama"

    @property
    def vanta_configured(self) -> bool:
        return bool(self.VANTA_API_KEY) and self.VANTA_INTEGRATION_MODE == "live"

    class Config:
        env_file = ".env"


settings = Settings()
