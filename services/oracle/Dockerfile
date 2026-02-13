# NPS V4 Oracle Service (multi-stage build)

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
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install only runtime dependencies (no compiler)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Framework available via volume mount (see docker-compose.yml)
# PYTHONPATH ensures both app code and framework are importable
ENV PYTHONPATH="/app:/app/numerology_ai_framework:${PYTHONPATH}"

# Create non-root user and logs directory
RUN groupadd -r oracle && useradd -r -g oracle -u 1000 oracle && \
    mkdir -p /app/logs && \
    chown -R oracle:oracle /app

EXPOSE 50052
EXPOSE 9090

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import grpc; ch = grpc.insecure_channel('localhost:50052'); grpc.channel_ready_future(ch).result(timeout=2)"

USER oracle

CMD ["python", "-m", "oracle_service.server"]
