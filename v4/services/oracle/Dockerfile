# NPS V4 Oracle Service
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

EXPOSE 50052

CMD ["python", "-m", "oracle_service.server"]
