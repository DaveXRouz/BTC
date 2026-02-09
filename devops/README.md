# NPS — DevOps & Monitoring

Production-grade monitoring for the Oracle gRPC service.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Oracle Service Container                           │
│                                                     │
│  ┌──────────────┐     ┌──────────────────────────┐ │
│  │ gRPC Server   │     │ HTTP Monitoring Sidecar  │ │
│  │ :50052        │     │ :9090                    │ │
│  │               │     │  GET /health             │ │
│  │ 8 RPCs with   │     │  GET /metrics            │ │
│  │ _track_rpc()  ├────▸│  GET /ready              │ │
│  │               │     │                          │ │
│  └──────────────┘     └──────────┬───────────────┘ │
│                                   │                  │
└───────────────────────────────────┼──────────────────┘
                                    │
              ┌─────────────────────┼──────────────────┐
              │                     │                   │
     ┌────────▼────────┐  ┌────────▼─────────┐  ┌─────▼──────┐
     │ Dashboard        │  │ Alerter           │  │ Prometheus  │
     │ Flask :9000      │  │ Telegram via      │  │ Scrapes     │
     │ Auto-refresh 5s  │  │ urllib, 30s loop  │  │ :9090       │
     └─────────────────┘  └──────────────────┘  └────────────┘
```

## Components

| Component              | Path                                     | Description                                 |
| ---------------------- | ---------------------------------------- | ------------------------------------------- |
| **Structured Logging** | `devops/logging/oracle_logger.py`        | JSON formatter + rotating file handlers     |
| **Metrics Collector**  | `devops/monitoring/oracle_metrics.py`    | Thread-safe per-RPC timing with percentiles |
| **HTTP Sidecar**       | `devops/monitoring/http_server.py`       | Stdlib HTTP server on port 9090             |
| **Dashboard**          | `devops/dashboards/simple_dashboard.py`  | Flask app on port 9000                      |
| **Telegram Alerter**   | `devops/alerts/oracle_alerts.py`         | Monitoring loop with cooldown-based alerts  |
| **Tests**              | `devops/tests/test_oracle_monitoring.py` | 28+ pytest tests                            |

## Environment Variables

| Variable               | Default                      | Description                                |
| ---------------------- | ---------------------------- | ------------------------------------------ |
| `LOG_LEVEL`            | `INFO`                       | Logging level (DEBUG/INFO/WARNING/ERROR)   |
| `ORACLE_LOG_DIR`       | `/app/logs`                  | Directory for log files                    |
| `ORACLE_HTTP_PORT`     | `9090`                       | HTTP monitoring sidecar port               |
| `ORACLE_HTTP_URL`      | `http://oracle-service:9090` | URL for dashboard/alerter to reach sidecar |
| `DASHBOARD_PORT`       | `9000`                       | Dashboard port                             |
| `NPS_BOT_TOKEN`        | _(empty)_                    | Telegram bot token for alerts              |
| `NPS_CHAT_ID`          | _(empty)_                    | Telegram chat ID for alerts                |
| `ALERT_CHECK_INTERVAL` | `30`                         | Seconds between alert checks               |
| `ALERT_COOLDOWN`       | `300`                        | Seconds between same-type alerts           |

## Quick Start

```bash
# Start Oracle with monitoring
docker compose up oracle-service -d

# Verify HTTP sidecar
curl http://localhost:9090/health | python -m json.tool
curl http://localhost:9090/metrics | python -m json.tool

# Start dashboard (requires flask)
pip install flask
ORACLE_HTTP_URL=http://localhost:9090 python -m devops.dashboards.simple_dashboard

# Start alerter
NPS_BOT_TOKEN=... NPS_CHAT_ID=... python -m devops.alerts.oracle_alerts

# Send test alert
NPS_BOT_TOKEN=... NPS_CHAT_ID=... python -m devops.alerts.oracle_alerts --test
```

## Running Tests

```bash
python -m pytest devops/tests/ -v
```

## Alert Types

| Level        | Condition                            | Cooldown |
| ------------ | ------------------------------------ | -------- |
| **CRITICAL** | Service unreachable or degraded      | 5 min    |
| **WARNING**  | Error rate > 5% or P95 > 10s         | 5 min    |
| **INFO**     | Service recovered from degraded/down | 5 min    |

## Graceful Degradation

All devops imports in `server.py` are wrapped in `try/except ImportError`. The Oracle service runs normally without the devops package — monitoring is purely additive.
