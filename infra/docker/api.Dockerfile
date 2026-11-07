FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends libexpat1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml README.md ./
COPY apps/api apps/api
COPY pipelines pipelines
COPY services services
RUN pip install --no-cache-dir -e . && useradd -m escudo && mkdir -p /var/lib/escudo/evidence && chown escudo /var/lib/escudo/evidence
COPY data data
COPY fixtures fixtures
USER escudo
EXPOSE 8000
CMD ["sh", "-c", "python -m escudo_api.etl_load && uvicorn escudo_api.main:app --host 0.0.0.0 --port 8000"]
