FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml README.md LICENSE ./
COPY crb65_score.py cli.py enrichment.py simulator.py ./
COPY agents ./agents

RUN python -m pip install --upgrade pip && \
    python -m pip install ".[server]"

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["crb65-service", "serve", "--host", "0.0.0.0", "--port", "8000"]
