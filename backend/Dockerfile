FROM python:3.15-slim@sha256:94d3426f1def7db4a106a232ac121bfd975393e5dfd40a619b955fae45fe7913

RUN groupadd --system app && useradd --system --gid app app

WORKDIR /app

COPY backend/requirements.txt /app/

RUN pip install --no-cache-dir --require-hashes -r requirements.txt && pip cache purge

COPY backend/ /app/
COPY data/ /app/data/
COPY templates/ /app/templates/

RUN chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
