FROM python:3.12-slim

RUN groupadd --system app && useradd --system --gid app app

RUN pip install --no-cache-dir \
    "fastapi[standard]" \
    "uvicorn[standard]" \
    "sqlalchemy[asyncio]" \
    asyncpg \
    alembic \
    "pydantic-settings" \
    pydantic \
    redis \
    httpx \
    structlog \
    sentry-sdk \
    slowapi \
    prometheus-fastapi-instrumentator \
    "passlib[bcrypt]" \
    "python-jose[cryptography]" \
    python-multipart \
    && pip cache purge

WORKDIR /app

COPY --chown=app:app . .

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
