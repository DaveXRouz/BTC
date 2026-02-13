#!/usr/bin/env python3
"""Database schema validation script for NPS.

Reads expected tables and indexes from database/schemas/*.sql,
connects to PostgreSQL, and validates they exist.

Usage:
    python3 scripts/validate_db_schema.py
    python3 scripts/validate_db_schema.py --host localhost --port 5432
"""

import argparse
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = PROJECT_ROOT / "database" / "schemas"

# Expected tables parsed from SQL files
EXPECTED_TABLES = {
    "oracle_users": "oracle_users.sql",
    "oracle_readings": "oracle_readings.sql",
    "oracle_reading_users": "oracle_reading_users.sql",
    "oracle_audit_log": "oracle_audit_log.sql",
    "oracle_settings": "oracle_settings.sql",
    "oracle_daily_readings": "oracle_daily_readings.sql",
    "telegram_daily_preferences": "telegram_daily_preferences.sql",
}

# Expected indexes parsed from schema files
EXPECTED_INDEXES = [
    # oracle_users
    "idx_oracle_users_name_birthday_active",
    "idx_oracle_users_created_at",
    "idx_oracle_users_name",
    "idx_oracle_users_coordinates",
    "idx_oracle_users_active",
    # oracle_readings
    "idx_oracle_readings_user_id",
    "idx_oracle_readings_primary_user_id",
    "idx_oracle_readings_created_at",
    "idx_oracle_readings_sign_type",
    "idx_oracle_readings_is_multi_user",
    "idx_oracle_readings_result_gin",
    "idx_oracle_readings_individual_gin",
    "idx_oracle_readings_compatibility_gin",
    "idx_oracle_readings_numerology_system",
    # oracle_reading_users
    "idx_oracle_reading_users_user_id",
    "idx_oracle_reading_users_reading_id",
    # oracle_audit_log
    "idx_oracle_audit_timestamp",
    "idx_oracle_audit_user",
    "idx_oracle_audit_action",
    "idx_oracle_audit_success",
    # oracle_settings
    "idx_oracle_settings_user_id",
    # oracle_daily_readings
    "idx_oracle_daily_readings_user_date",
    "idx_oracle_daily_readings_date",
    "idx_oracle_daily_readings_result_gin",
    # telegram_daily_preferences
    "idx_telegram_daily_enabled",
    "idx_telegram_daily_chat_id",
]


def parse_tables_from_sql(schemas_dir: Path) -> list[str]:
    """Extract CREATE TABLE names from all SQL files in schemas_dir."""
    tables = []
    pattern = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", re.IGNORECASE
    )
    for sql_file in sorted(schemas_dir.glob("*.sql")):
        text = sql_file.read_text()
        for match in pattern.finditer(text):
            tables.append(match.group(1))
    return tables


def parse_indexes_from_sql(schemas_dir: Path) -> list[str]:
    """Extract CREATE INDEX names from all SQL files in schemas_dir."""
    indexes = []
    pattern = re.compile(
        r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)",
        re.IGNORECASE,
    )
    for sql_file in sorted(schemas_dir.glob("*.sql")):
        text = sql_file.read_text()
        for match in pattern.finditer(text):
            indexes.append(match.group(1))
    return indexes


def get_connection(host: str, port: int, dbname: str, user: str, password: str):
    """Create a PostgreSQL connection using psycopg2."""
    try:
        import psycopg2
    except ImportError:
        print(
            "ERROR: psycopg2 not installed. Install with: pip install psycopg2-binary"
        )
        sys.exit(1)

    try:
        conn = psycopg2.connect(
            host=host, port=port, dbname=dbname, user=user, password=password
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"ERROR: Cannot connect to PostgreSQL at {host}:{port}/{dbname}")
        print(f"  {e}")
        print("\nMake sure PostgreSQL is running:")
        print("  docker-compose up -d postgres")
        sys.exit(1)


def check_tables(cursor, expected: list[str]) -> tuple[list[str], list[str]]:
    """Check which expected tables exist. Returns (found, missing)."""
    cursor.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
    )
    existing = {row[0] for row in cursor.fetchall()}

    found = [t for t in expected if t in existing]
    missing = [t for t in expected if t not in existing]
    return found, missing


def check_indexes(cursor, expected: list[str]) -> tuple[list[str], list[str]]:
    """Check which expected indexes exist. Returns (found, missing)."""
    cursor.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
    existing = {row[0] for row in cursor.fetchall()}

    found = [i for i in expected if i in existing]
    missing = [i for i in expected if i not in existing]
    return found, missing


def check_triggers(cursor) -> list[str]:
    """List triggers on public tables."""
    cursor.execute(
        "SELECT trigger_name, event_object_table "
        "FROM information_schema.triggers "
        "WHERE trigger_schema = 'public'"
    )
    return [f"{row[0]} ON {row[1]}" for row in cursor.fetchall()]


def print_report(
    tables_found: list[str],
    tables_missing: list[str],
    indexes_found: list[str],
    indexes_missing: list[str],
    triggers: list[str],
) -> bool:
    """Print validation report. Returns True if all checks pass."""
    total_tables = len(tables_found) + len(tables_missing)
    total_indexes = len(indexes_found) + len(indexes_missing)
    all_pass = len(tables_missing) == 0 and len(indexes_missing) == 0

    print("=" * 60)
    print("  NPS Database Schema Validation Report")
    print("=" * 60)

    # Tables
    print(f"\n  Tables: {len(tables_found)}/{total_tables} present")
    for t in tables_found:
        print(f"    [PASS] {t}")
    for t in tables_missing:
        print(f"    [FAIL] {t} — MISSING")

    # Indexes
    print(f"\n  Indexes: {len(indexes_found)}/{total_indexes} present")
    for i in indexes_found:
        print(f"    [PASS] {i}")
    for i in indexes_missing:
        print(f"    [FAIL] {i} — MISSING")

    # Triggers
    print(f"\n  Triggers found: {len(triggers)}")
    for t in triggers:
        print(f"    {t}")

    # Summary
    print("\n" + "=" * 60)
    if all_pass:
        print("  RESULT: ALL CHECKS PASSED")
    else:
        fails = len(tables_missing) + len(indexes_missing)
        print(f"  RESULT: {fails} CHECK(S) FAILED")
    print("=" * 60)

    return all_pass


def main():
    parser = argparse.ArgumentParser(description="Validate NPS database schema")
    parser.add_argument("--host", default=os.environ.get("POSTGRES_HOST", "localhost"))
    parser.add_argument(
        "--port", type=int, default=int(os.environ.get("POSTGRES_PORT", "5432"))
    )
    parser.add_argument("--dbname", default=os.environ.get("POSTGRES_DB", "nps"))
    parser.add_argument("--user", default=os.environ.get("POSTGRES_USER", "nps"))
    parser.add_argument("--password", default=os.environ.get("POSTGRES_PASSWORD", ""))
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse schemas only, no DB connection"
    )
    args = parser.parse_args()

    # Parse expected schema from SQL files
    print(f"Parsing schemas from: {SCHEMAS_DIR}")
    parsed_tables = parse_tables_from_sql(SCHEMAS_DIR)
    parsed_indexes = parse_indexes_from_sql(SCHEMAS_DIR)
    print(f"  Found {len(parsed_tables)} table definitions")
    print(f"  Found {len(parsed_indexes)} index definitions")

    if args.dry_run:
        print("\n--dry-run: Skipping database connection")
        print("\nExpected tables:")
        for t in parsed_tables:
            print(f"  {t}")
        print("\nExpected indexes:")
        for i in parsed_indexes:
            print(f"  {i}")
        sys.exit(0)

    # Connect and validate
    conn = get_connection(args.host, args.port, args.dbname, args.user, args.password)
    cursor = conn.cursor()

    try:
        tables_found, tables_missing = check_tables(
            cursor, list(EXPECTED_TABLES.keys())
        )
        indexes_found, indexes_missing = check_indexes(cursor, EXPECTED_INDEXES)
        triggers = check_triggers(cursor)

        all_pass = print_report(
            tables_found,
            tables_missing,
            indexes_found,
            indexes_missing,
            triggers,
        )
        sys.exit(0 if all_pass else 1)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
