"""Fixtures de integración: base PostGIS de tests separada (DATABASE_URL_TEST)."""

from __future__ import annotations

import os

import pytest

TEST_URL = os.environ.get("DATABASE_URL_TEST", "postgresql+psycopg://escudo:escudo_dev_only@localhost:5433/escudo_test")
os.environ["DATABASE_URL"] = TEST_URL  # antes de importar escudo_api (engine se crea al importar)
os.environ.setdefault("ESCUDO_JWT_SECRET", "test-secret-with-at-least-32-bytes-0123456789")


def _db_available() -> bool:
    import sqlalchemy

    try:
        with sqlalchemy.create_engine(TEST_URL).connect():
            return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def loaded_db(tmp_path_factory):
    if not _db_available():
        pytest.skip("PostGIS de tests no disponible (docker compose -f infra/docker-compose.yml up -d db)")
    from escudo_api.config import settings

    settings.escudo_evidence_dir = tmp_path_factory.mktemp("evidence")
    from escudo_api import etl_load

    load_idem = os.environ.get("ESCUDO_TEST_LOAD_IDEM", "0") == "1"
    args = ["--reset"] + ([] if load_idem else ["--skip-idem"])
    assert etl_load.main(args) == 0
    return True


@pytest.fixture()
def client(loaded_db):
    from fastapi.testclient import TestClient

    from escudo_api.main import app

    return TestClient(app)


def _login(client, email: str) -> dict:
    r = client.post("/v1/auth/login", json={"email": email, "password": "demo-escudo-2026"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def auth_a(client):
    return _login(client, "gestor@demo.escudo.local")


@pytest.fixture()
def auth_b(client):
    return _login(client, "gestor-b@demo.escudo.local")
