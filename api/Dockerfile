# NPS V4 API Service (multi-stage build)

# ─── Stage 1: Builder ───
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies to /install prefix
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# ─── Stage 2: Runtime ───
FROM python:3.11-slim

WORKDIR /app

# Install only runtime dependencies (no compiler)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r api && useradd -r -g api -u 1001 api && \
    chown -R api:api /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

USER api

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "warning"]
