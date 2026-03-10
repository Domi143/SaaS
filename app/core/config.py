from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = Field("development", alias="APP_ENV")
    debug: bool = Field(True, alias="DEBUG")

    secret_key: str = Field(..., alias="SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_minutes: int = Field(
        60 * 24 * 30, alias="JWT_REFRESH_TOKEN_EXPIRE_MINUTES"
    )

    app_host: str = Field("0.0.0.0", alias="APP_HOST")
    app_port: int = Field(8000, alias="APP_PORT")

    backend_cors_origins: List[AnyHttpUrl] = Field(default_factory=list, alias="BACKEND_CORS_ORIGINS")

    database_url: str = Field(..., alias="DATABASE_URL")

    file_storage_backend: str = Field("local", alias="FILE_STORAGE_BACKEND")
    file_storage_path: str = Field("/data/storage", alias="FILE_STORAGE_PATH")

    default_plan_name: str = Field("free", alias="DEFAULT_PLAN_NAME")

    paddle_env: str = Field("sandbox", alias="PADDLE_ENV")
    paddle_vendor_id: str | None = Field(None, alias="PADDLE_VENDOR_ID")
    paddle_api_key: str | None = Field(None, alias="PADDLE_API_KEY")
    paddle_webhook_secret: str | None = Field(None, alias="PADDLE_WEBHOOK_SECRET")
    paddle_price_id_free: str | None = Field(None, alias="PADDLE_PRICE_ID_FREE")
    paddle_price_id_plus: str | None = Field(None, alias="PADDLE_PRICE_ID_PLUS")
    paddle_price_id_pro: str | None = Field(None, alias="PADDLE_PRICE_ID_PRO")

    log_level: str = Field("info", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            return parts
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()

