#!/usr/bin/env bash
# Arranque local completo de ESCUDO MADRID (Linux/macOS/Git Bash).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python; [ -x "$PY" ] || PY=.venv/Scripts/python
[ -x "$PY" ] || { python -m venv .venv; PY=$([ -x .venv/bin/python ] && echo .venv/bin/python || echo .venv/Scripts/python); }
"$PY" -m pip install -q -e ".[dev]"
docker compose -f infra/docker-compose.yml up -d db
until docker compose -f infra/docker-compose.yml exec -T db pg_isready -U escudo -q; do sleep 2; done
[ -f data/raw/CAM-01/manifest.json ] && ls data/raw/CAM-01/*.csv >/dev/null 2>&1 || "$PY" -m escudo_pipelines.fetch
"$PY" -m escudo_pipelines.cam_transform
[ -f data/processed/idem/municipal_class_shares.csv ] || { "$PY" -m escudo_pipelines.idem.fetch && "$PY" -m escudo_pipelines.idem.transform; }
"$PY" -m escudo_api.etl_load
echo "API: $PY -m uvicorn escudo_api.main:app --port 8000   |   Web: (cd apps/web && npm install && npm run dev)"
