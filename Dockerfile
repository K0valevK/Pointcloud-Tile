# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# PDAL и laszip для обработки LiDAR
RUN apt-get update && apt-get install -y --no-install-recommends \
    pdal \
    libpdal-dev \
    liblaszip-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- dependencies stage ---
FROM base AS deps

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip && \
    pip install .

# --- runtime stage ---
FROM base AS runtime

COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY --from=deps /app/src /app/src
COPY pyproject.toml README.md ./

RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /data/tiles /data/layers /data/checkpoints && \
    chown -R appuser:appuser /data /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/layers || exit 1

CMD ["pointcloud-tile", "serve", "--host", "0.0.0.0", "--port", "8000"]
