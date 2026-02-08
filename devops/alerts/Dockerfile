# NPS V4 Oracle Alerter
FROM python:3.11-slim-bookworm

WORKDIR /app

# Copy devops package
COPY . /app/devops/

# No pip dependencies needed (stdlib only)

# Create non-root user
RUN groupadd -r alerter && useradd -r -g alerter -u 1001 alerter && \
    chown -R alerter:alerter /app
USER alerter

CMD ["python", "-m", "devops.alerts.oracle_alerts"]
