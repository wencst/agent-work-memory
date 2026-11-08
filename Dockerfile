FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . \
    && useradd --system --uid 10001 --create-home awm \
    && mkdir -p /data \
    && chown -R awm:awm /app /data

USER awm
ENV AWM_HOST=0.0.0.0 \
    AWM_PORT=8765 \
    AWM_DATABASE_PATH=/data/memory.sqlite3
EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8765/health', timeout=2)"

CMD ["awm", "serve"]
