FROM python:3.12-slim@sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203

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
