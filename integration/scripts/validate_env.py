#!/usr/bin/env python3
"""Validate that all required environment variables are set and services are reachable."""

import os
import sys
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parents[2] / ".env"


def load_env(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict."""
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def check_required(env: dict[str, str]) -> list[str]:
    """Check that critical env vars have non-default values."""
    issues = []
    required = {
        "POSTGRES_PASSWORD": "changeme",
        "API_SECRET_KEY": "changeme-generate-a-real-secret",
        "NPS_ENCRYPTION_KEY": "",
        "NPS_ENCRYPTION_SALT": "",
    }
    for key, bad_value in required.items():
        val = env.get(key, "")
        if not val or val == bad_value:
            issues.append(f"  {key}: missing or still default value")
    return issues


def check_postgres(env: dict[str, str]) -> str:
    """Try connecting to PostgreSQL."""
    try:
        import psycopg2

        conn = psycopg2.connect(
            host=env.get("POSTGRES_HOST", "localhost"),
            port=int(env.get("POSTGRES_PORT", "5432")),
            dbname=env.get("POSTGRES_DB", "nps"),
            user=env.get("POSTGRES_USER", "nps"),
            password=env.get("POSTGRES_PASSWORD", ""),
            connect_timeout=5,
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return "OK"
    except ImportError:
        try:
            from sqlalchemy import create_engine, text

            url = (
                f"postgresql://{env.get('POSTGRES_USER', 'nps')}:"
                f"{env.get('POSTGRES_PASSWORD', '')}@"
                f"{env.get('POSTGRES_HOST', 'localhost')}:"
                f"{env.get('POSTGRES_PORT', '5432')}/"
                f"{env.get('POSTGRES_DB', 'nps')}"
            )
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            return "OK"
        except Exception as e:
            return f"FAIL ({e})"
    except Exception as e:
        return f"FAIL ({e})"


def check_redis(env: dict[str, str]) -> str:
    """Try connecting to Redis."""
    try:
        import redis

        r = redis.Redis(
            host=env.get("REDIS_HOST", "localhost"),
            port=int(env.get("REDIS_PORT", "6379")),
            socket_timeout=5,
        )
        r.ping()
        r.close()
        return "OK"
    except ImportError:
        return "SKIP (redis package not installed)"
    except Exception as e:
        return f"FAIL ({e})"


def main():
    print("=" * 60)
    print("NPS Environment Validation")
    print("=" * 60)

    # Load env
    env = load_env(env_path)
    if not env:
        print(f"\nERROR: No .env file found at {env_path}")
        print("  Copy .env.example to .env and fill in values.")
        sys.exit(1)

    print(f"\n.env loaded from: {env_path}")
    print(f"  Variables found: {len(env)}")

    # Check required values
    print("\n--- Required Variables ---")
    issues = check_required(env)
    if issues:
        print("ISSUES:")
        for issue in issues:
            print(issue)
    else:
        print("  All required variables set.")

    # Check services
    print("\n--- Service Connectivity ---")

    pg_status = check_postgres(env)
    print(f"  PostgreSQL: {pg_status}")

    redis_status = check_redis(env)
    print(f"  Redis:      {redis_status}")

    # Summary
    print("\n--- Summary ---")
    all_ok = not issues and "FAIL" not in pg_status and "FAIL" not in redis_status
    if all_ok:
        print("  All checks passed. Ready for integration tests.")
    else:
        print("  Some checks failed. Fix issues before running tests.")

    print("=" * 60)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
