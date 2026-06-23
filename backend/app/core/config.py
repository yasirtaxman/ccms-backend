from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "CCMS API"
    ENVIRONMENT: str = "local"
    DEBUG: bool = False
    API_V1_PREFIX: str = ""
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3001", "http://127.0.0.1:3001",
    ]
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60
    LOG_LEVEL: str = "INFO"
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1", "testserver"]
    EXPORT_MAX_ROWS: int = 5000
    IMPORT_MAX_ROWS: int = 5000
    ADMIN_USERNAME: str | None = None
    ADMIN_PASSWORD: str | None = None

    @field_validator("BACKEND_CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_list(cls, value):
        if isinstance(value, str) and not value.strip().startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def upload_path(self) -> Path:
        return Path(self.UPLOAD_DIR).resolve()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
