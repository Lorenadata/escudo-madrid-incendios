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

# Valores de ejemplo publicados en el repositorio: con ellos cualquiera podría firmar tokens válidos.
_PUBLISHED_SECRETS = {"dev-only-change-me", "cambia-esto-por-un-secreto-de-al-menos-32-bytes", ""}
JWT_SECRET_EPHEMERAL = (settings.escudo_jwt_secret in _PUBLISHED_SECRETS
                        or len(settings.escudo_jwt_secret.encode()) < 32)
if JWT_SECRET_EPHEMERAL:
    import logging
    import secrets

    settings.escudo_jwt_secret = secrets.token_urlsafe(48)
    logging.getLogger("escudo.security").warning(
        "ESCUDO_JWT_SECRET ausente, débil o de ejemplo: se usa un secreto aleatorio de este proceso "
        "(las sesiones caducan al reiniciar). Configure un secreto propio de ≥32 bytes en producción.")
