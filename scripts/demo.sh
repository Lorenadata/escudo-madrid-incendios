#!/usr/bin/env bash
# Demo de ESCUDO MADRID en un comando (ROADMAP 1.5).
#   bash scripts/demo.sh          arranca BD + API + web, recarga la demo FICTICIA y calienta cachés
#   bash scripts/demo.sh stop     detiene API y web arrancadas por este script
#   bash scripts/demo.sh check    ejecuta los e2e contra la demo levantada (y vuelve a limpiar la demo)
# Variables: API_PORT (8000), WEB_PORT (3000).
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)
API_PORT=${API_PORT:-8000}
WEB_PORT=${WEB_PORT:-3000}
PY=.venv/bin/python; [ -x "$PY" ] || PY=.venv/Scripts/python
PIDS=var/demo.pids
mkdir -p var var/aemet-cache
export ESCUDO_AEMET_CACHE_DIR="$ROOT/var/aemet-cache"
export CORS_ORIGINS="http://localhost:$WEB_PORT,http://127.0.0.1:$WEB_PORT"

say() { printf '\033[1m[demo]\033[0m %s\n' "$*"; }

stop() {
  if [ -f "$PIDS" ]; then
    while read -r pid; do kill "$pid" 2>/dev/null || true; done < "$PIDS"
    rm -f "$PIDS"
    say "API y web detenidas."
  else
    say "No hay procesos registrados en $PIDS."
  fi
}

wait_url() {  # wait_url URL segundos
  for _ in $(seq 1 "$2"); do curl -s -m 2 -o /dev/null "$1" && return 0; sleep 1; done
  return 1
}

reseed() { "$PY" -m escudo_api.etl_load --skip-idem > var/demo-seed.log 2>&1; }

case "${1:-start}" in
  stop) stop; exit 0 ;;
  check)
    E2E_API_PORT=$(cat var/demo-api-port 2>/dev/null || echo "$API_PORT")
    rc=0; (cd apps/web && E2E_BASE_URL="http://localhost:$WEB_PORT" E2E_API_URL="http://localhost:$E2E_API_PORT" npx playwright test) || rc=$?
    reseed  # siempre: borra los ámbitos creados por los tests
    if [ "$rc" -eq 0 ]; then say "e2e en verde y demo restaurada."; else say "e2e con fallos (demo restaurada igualmente)."; fi
    exit "$rc" ;;
  start) ;;
  *) echo "uso: $0 [start|stop|check]"; exit 2 ;;
esac

[ -x "$PY" ] || { say "Falta el entorno Python: python -m venv .venv && .venv/Scripts/python -m pip install -e '.[dev]'"; exit 1; }
stop >/dev/null 2>&1 || true

say "1/6 Base de datos PostGIS"
docker compose -f infra/docker-compose.yml up -d db >/dev/null
until docker compose -f infra/docker-compose.yml exec -T db pg_isready -U escudo -q; do sleep 2; done

say "2/6 Esquema (Alembic) y datos"
"$PY" -m alembic upgrade head > var/demo-migrate.log 2>&1 || {
  # una BD creada antes de las migraciones: se marca la revisión inicial y se migra
  "$PY" -m alembic stamp 38bbf38b9c9a >> var/demo-migrate.log 2>&1 && "$PY" -m alembic upgrade head >> var/demo-migrate.log 2>&1; }
[ -f data/processed/cam/municipal_indicators.csv ] || { "$PY" -m escudo_pipelines.fetch && "$PY" -m escudo_pipelines.cam_transform; }
HAS_IDEM=$(docker compose -f infra/docker-compose.yml exec -T db psql -U escudo -d escudo -tAc \
  "select count(*) from official_layer_municipal_shares" 2>/dev/null | tr -d '[:space:]' || echo 0)
if [ "${HAS_IDEM:-0}" -gt 0 ]; then reseed; else "$PY" -m escudo_api.etl_load > var/demo-seed.log 2>&1; fi
say "    datos cargados; demo FICTICIA restaurada (sin ámbitos de pruebas)"

say "3/6 API en :$API_PORT"
if curl -s -m 2 -o /dev/null "http://127.0.0.1:$API_PORT/"; then
  say "El puerto $API_PORT ya está ocupado por otro servicio. Usa otro: API_PORT=8010 bash scripts/demo.sh"; exit 1
fi
nohup "$PY" -m uvicorn escudo_api.main:app --host 127.0.0.1 --port "$API_PORT" > var/demo-api.log 2>&1 &
echo $! > "$PIDS"
wait_url "http://127.0.0.1:$API_PORT/health" 60 || { say "La API no arrancó: var/demo-api.log"; exit 1; }

say "4/6 Web en :$WEB_PORT"
cd apps/web
[ -d node_modules ] || npm ci >/dev/null
# Recompila si no hay build, si cambió el código o si cambió el puerto de la API (va incrustado en el build)
if [ ! -f .next/BUILD_ID ] || [ -n "$(find src -newer .next/BUILD_ID -type f | head -1)" ]    || [ "$(cat "$ROOT/var/demo-api-port" 2>/dev/null)" != "$API_PORT" ]; then
  NEXT_PUBLIC_API_URL="http://localhost:$API_PORT" npm run build > "$ROOT/var/demo-build.log" 2>&1
  echo "$API_PORT" > "$ROOT/var/demo-api-port"
fi
# siempre DESPUÉS del build: un servidor previo serviría chunks inexistentes
nohup node node_modules/next/dist/bin/next start -p "$WEB_PORT" > "$ROOT/var/demo-web.log" 2>&1 &
echo $! >> "$ROOT/$PIDS"
cd "$ROOT"
wait_url "http://localhost:$WEB_PORT/" 60 || { say "La web no arrancó: var/demo-web.log"; exit 1; }

say "5/6 Calentando API y caché AEMET (municipios de la demo)"
[ "${DEMO_NO_WARMUP:-0}" = "1" ] && say "    (omitido: DEMO_NO_WARMUP=1)" || for path in /v1/sources /v1/layers /v1/layers/municipalities/geojson /v1/layers/risk/geojson \
            /v1/municipalities/28131/profile /v1/municipalities/28079/profile /v1/demo/guided \
            /v1/analysis/municipal-matrix /v1/demo/report.pdf; do
  curl -s -m 60 -o /dev/null -w "    %{http_code} ${path} (%{time_total}s)\n" "http://127.0.0.1:$API_PORT$path"
done
W=$(curl -s "http://127.0.0.1:$API_PORT/v1/weather/context?municipality_code=28131" | "$PY" -c \
  "import json,sys;d=json.load(sys.stdin);print(d['status'], d.get('issued_at') or d.get('last_valid_at') or '')")
say "    AEMET 28131: $W (sin red se mostrará este dato con su fecha mientras sea válido, y después «no disponible»)"

say "6/6 Listo"
cat <<EOF

  Web:  http://localhost:$WEB_PORT          Caso guiado: http://localhost:$WEB_PORT/demo
  API:  http://localhost:$API_PORT/docs
  Cuentas FICTICIAS (contraseña demo-escudo-2026):
    gestor@demo.escudo.local     gestión de la urbanización
    tecnico@demo.escudo.local    técnico SIN cualificación verificada
    municipal@demo.escudo.local  responsable municipal (Flujo B)
  Plan B sin servidor: artifacts/demo-screenshots/ y el PDF de /v1/demo/report.pdf
  Parar: bash scripts/demo.sh stop      Comprobar: bash scripts/demo.sh check
EOF
