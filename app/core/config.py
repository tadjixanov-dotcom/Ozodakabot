"""Markazlashgan konfiguratsiya — barcha sozlamalar .env faylidan o'qiladi."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Telegram
    bot_token: str = ""
    admin_ids: str = ""

    # Ma'lumotlar bazasi
    database_url: str = "sqlite+aiosqlite:///./news_bot.db"

    # Standart foydalanuvchi sozlamalari
    default_timezone: str = "Asia/Tashkent"
    default_language: str = "uz"
    default_daily_limit: int = 10

    # Tashqi API'lar
    news_api_key: str = ""
    gdelt_enabled: bool = True

    # AI provayder (bo'sh bo'lsa AIsiz rejim)
    ai_provider: str = ""
    ai_api_key: str = ""
    ai_model: str = "claude-opus-4-8"

    log_level: str = "INFO"

    # Yig'ish / yuborish parametrlari
    fetch_interval_minutes: int = 15
    digest_check_interval_minutes: int = 5
    max_article_age_hours: int = 48
    realtime_importance_threshold: float = 0.8
    critical_importance_threshold: float = 0.9
    max_messages_per_hour: int = 20
    dedup_title_threshold: float = 0.85
    dislike_similarity_threshold: float = 0.5
    dislike_block_threshold: float = 0.72
    exploration_rate: float = 0.12
    request_timeout_seconds: float = 20.0
    sources_config_path: str = str(BASE_DIR / "config" / "sources.json")

    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, value: str) -> str:
        """Railway/Heroku beradigan postgres:// URL'ni async driverga moslaydi."""
        if value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql://", 1)
        if value.startswith("postgresql://"):
            value = value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @property
    def admin_id_list(self) -> list[int]:
        raw = str(self.admin_ids).replace(";", ",")
        return [int(p) for p in (x.strip() for x in raw.split(",")) if p.isdigit()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
