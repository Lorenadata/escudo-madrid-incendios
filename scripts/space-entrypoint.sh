#!/usr/bin/env bash
# Arranque de la demo pública en un único contenedor (Hugging Face Space, ver infra/docker/space.Dockerfile).
# PostGIS local (solo 127.0.0.1) → migraciones → datos reales + demo FICTICIA → API (:8000, interna) → web (:7860).
# El disco del Space es efímero: cada reinicio parte de cero y restaura la demo ficticia.
set -euo pipefail
cd /app
log() { printf '[space] %s\n' "$*"; }

PGBIN=$(ls -d /usr/lib/postgresql/*/bin | sort -V | tail -1)
export PGDATA=${PGDATA:-/tmp/pgdata} PGHOST=127.0.0.1 PGPORT=5432 PGUSER=escudo
mkdir -p /tmp/evidence /tmp/aemet-cache /tmp/pgsock

log "1/5 PostGIS local"
if [ ! -s "$PGDATA/PG_VERSION" ]; then
  "$PGBIN/initdb" -D "$PGDATA" -U escudo --auth=trust --encoding=UTF8 --locale=C.UTF-8 >/tmp/initdb.log
fi
"$PGBIN/pg_ctl" -D "$PGDATA" -l /tmp/postgres.log -w \
  -o "-c listen_addresses=127.0.0.1 -c unix_socket_directories=/tmp/pgsock -c shared_buffers=256MB" start
psql -d postgres -tAc "select 1 from pg_database where datname='escudo'" | grep -q 1 || createdb escudo
psql -d escudo -qc "create extension if not exists postgis"

export DATABASE_URL="postgresql+psycopg://escudo@127.0.0.1:5432/escudo"
# Sin secreto configurado se genera uno aleatorio por arranque (las sesiones caducan al reiniciar).
export ESCUDO_JWT_SECRET="${ESCUDO_JWT_SECRET:-$(python -c 'import secrets;print(secrets.token_urlsafe(48))')}"
export ESCUDO_EVIDENCE_DIR=/tmp/evidence ESCUDO_AEMET_CACHE_DIR=/tmp/aemet-cache
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:7860}"

log "2/5 Esquema (Alembic)"
python -m alembic upgrade head

log "3/5 Datos reales (Portal CAM, IDEM) y demo FICTICIA etiquetada"
python -m escudo_api.etl_load

log "4/5 API interna en 127.0.0.1:8000 (expuesta como /api)"
python -m uvicorn escudo_api.main:app --host 127.0.0.1 --port 8000 --root-path /api --proxy-headers &
API_PID=$!
for _ in $(seq 1 90); do curl -sf -o /dev/null http://127.0.0.1:8000/health && break; sleep 1; done

log "5/5 Web en 0.0.0.0:7860"
cd /app/apps/web
node node_modules/next/dist/bin/next start -H 0.0.0.0 -p 7860 &
WEB_PID=$!
# Calentamiento en segundo plano: geometrías y caso guiado quedan en caché antes de la primera visita.
( sleep 5; for p in /v1/layers/municipalities/geojson /v1/layers/risk/geojson /v1/demo/guided /v1/analysis/municipal-matrix; do
    curl -s -m 120 -o /dev/null "http://127.0.0.1:8000$p"; done; log "cachés calentadas" ) &

trap 'kill $WEB_PID $API_PID 2>/dev/null; "$PGBIN/pg_ctl" -D "$PGDATA" -m fast stop' TERM INT
wait -n $WEB_PID $API_PID
log "un proceso terminó; saliendo para que el Space reinicie"
exit 1
