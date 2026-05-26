FROM python:3.12-slim

RUN groupadd --system app && useradd --system --gid app app

WORKDIR /app

COPY backend/pyproject.toml /app/

RUN pip install --no-cache-dir -e . && pip cache purge

COPY backend/ /app/
COPY data/ /app/data/
COPY templates/ /app/templates/

RUN chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
