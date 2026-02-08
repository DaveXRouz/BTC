# NPS V4 Oracle Service
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies (before code copy for layer caching)
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

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
