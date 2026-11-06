from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    database_url: str = "postgresql+psycopg://escudo:escudo_dev_only@localhost:5433/escudo"
    escudo_jwt_secret: str = "dev-only-change-me"
    jwt_ttl_minutes: int = 480
    aemet_api_key: str | None = None
    escudo_evidence_dir: Path = REPO_ROOT / "var" / "evidence"
    data_dir: Path = REPO_ROOT / "data"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    max_evidence_bytes: int = 10 * 1024 * 1024
    version: str = "0.1.0"


settings = Settings()
