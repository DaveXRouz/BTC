"""
Migrate legacy session files to current PostgreSQL.

Legacy format: nps/data/sessions/{session_id}.json
  Each file: {"session_id": "...", "terminal_id": "...", "started": epoch, ...}

Current target: sessions table
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def migrate_sessions(v3_path: Path, dry_run: bool = True, **kwargs):
    """Migrate legacy session JSON files to current PostgreSQL sessions table."""
    sessions_dir = v3_path / "data" / "sessions"

    if not sessions_dir.exists():
        logger.info("No sessions directory found — skipping")
        return

    session_files = list(sessions_dir.glob("*.json"))
    # Exclude _meta.json files (vault session metadata, not scan sessions)
    session_files = [f for f in session_files if not f.name.endswith("_meta.json")]

    logger.info(f"  Found {len(session_files)} session files")

    if dry_run:
        for sf in session_files[:5]:
            try:
                with open(sf) as f:
                    data = json.load(f)
                logger.info(
                    f"    {sf.name}: terminal={data.get('terminal_id', '?')}, "
                    f"duration={data.get('duration', 0):.0f}s"
                )
            except (json.JSONDecodeError, IOError):
                logger.warning(f"    {sf.name}: corrupt or unreadable")
        if len(session_files) > 5:
            logger.info(f"    ... and {len(session_files) - 5} more")
        logger.info(f"  Would INSERT {len(session_files)} rows into sessions table")
        return

    # TODO: Implement actual migration
    # 1. For each session file:
    #    a. Parse JSON
    #    b. Convert epoch timestamps to datetime
    #    c. Generate UUID
    #    d. Map legacy fields to current schema
    #    e. INSERT into sessions table
    logger.info("  [STUB] Live migration not yet implemented")
