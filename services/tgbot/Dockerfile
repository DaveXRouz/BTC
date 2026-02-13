FROM python:3.11-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source into a proper package
COPY . /app/tgbot/

# Create non-root user
RUN groupadd -r botuser && useradd -r -g botuser -u 1001 botuser && \
    chown -R botuser:botuser /app
USER botuser

CMD ["python", "-m", "tgbot"]
