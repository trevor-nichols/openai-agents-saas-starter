# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /repo

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY packages/starter_contracts packages/starter_contracts
COPY packages/starter_providers packages/starter_providers
COPY apps/api-service apps/api-service

RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

RUN pip install --upgrade pip \
 && pip install --no-cache-dir /repo/packages/starter_contracts \
 && pip install --no-cache-dir /repo/packages/starter_providers

WORKDIR /repo/apps/api-service

RUN pip install --no-cache-dir .

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

COPY --from=builder /repo/apps/api-service/src /app/src
COPY --from=builder /repo/apps/api-service/alembic /app/alembic
COPY --from=builder /repo/apps/api-service/alembic.ini /app/alembic.ini

RUN mkdir -p /app/var/keys \
  && chown -R appuser:appuser /app/var/keys

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready').read()"

USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "/app/src"]
