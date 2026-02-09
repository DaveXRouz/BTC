"""
Migrate legacy oracle readings to current PostgreSQL.

Legacy format: nps/data/oracle_readings.json (if exists)
  JSON array of reading objects

Current target: readings table
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def migrate_readings(v3_path: Path, dry_run: bool = True, **kwargs):
    """Migrate legacy oracle readings to current PostgreSQL."""
    readings_file = v3_path / "data" / "oracle_readings.json"

    if not readings_file.exists():
        logger.info("No oracle readings file found — skipping")
        return

    try:
        with open(readings_file) as f:
            readings = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"  Failed to read oracle readings: {e}")
        return

    if not isinstance(readings, list):
        logger.error("  Oracle readings file is not a JSON array")
        return

    logger.info(f"  Found {len(readings)} oracle readings")

    if dry_run:
        logger.info(f"  Would INSERT {len(readings)} rows into readings table")
        return

    # TODO: Implement actual migration
    logger.info("  [STUB] Live migration not yet implemented")
