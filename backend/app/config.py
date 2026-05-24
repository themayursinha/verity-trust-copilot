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

    class Config:
        env_file = ".env"


settings = Settings()
