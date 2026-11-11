# Demo pública de ESCUDO MADRID en un único contenedor (Hugging Face Spaces, sdk: docker, app_port 7860).
# Clona el repositorio público en un commit fijo: lo desplegado es exactamente el código abierto auditable.
#   docker build -f infra/docker/space.Dockerfile --build-arg REPO_REF=<commit> -t escudo-space .
#   docker run --rm -p 7860:7860 escudo-space
ARG REPO_URL=https://github.com/Lorenadata/escudo-madrid-incendios.git
ARG REPO_REF=main

FROM alpine/git:2.47.2 AS src
ARG REPO_URL
ARG REPO_REF
RUN git clone --filter=blob:none "$REPO_URL" /src && cd /src && git checkout "$REPO_REF" && rm -rf .git artifacts

FROM node:24-bookworm-slim AS web
WORKDIR /web
COPY --from=src /src/apps/web/package*.json ./
RUN npm ci --no-audit --no-fund
COPY --from=src /src/apps/web ./
ENV NEXT_PUBLIC_API_URL=/api ESCUDO_API_PROXY=http://127.0.0.1:8000 NEXT_TELEMETRY_DISABLED=1     ESCUDO_FRAME_ANCESTORS="https://huggingface.co"
RUN npm run build && npm prune --omit=dev

FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 \
    ESCUDO_API_PROXY=http://127.0.0.1:8000
RUN apt-get update && apt-get install -y --no-install-recommends \
      postgresql-15 postgresql-15-postgis-3 libexpat1 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=web /usr/local/bin/node /usr/local/bin/node
RUN useradd -m -u 1000 user
WORKDIR /app
COPY --from=src --chown=user /src /app
RUN pip install --no-cache-dir -e . && rm -rf /app/apps/web/node_modules
COPY --from=web --chown=user /web /app/apps/web
RUN chmod +x /app/scripts/space-entrypoint.sh
USER user
EXPOSE 7860
CMD ["/app/scripts/space-entrypoint.sh"]
