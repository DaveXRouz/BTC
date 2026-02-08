"""
Migrate V3 learning state to V4 PostgreSQL.

V3 format: nps/data/learning/learning_state.json
  Single JSON: {"xp": N, "level": N, "insights": [...], ...}

V4 target: learning_data + insights tables
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def migrate_learning(v3_path: Path, dry_run: bool = True, **kwargs):
    """Migrate V3 learning state to V4 PostgreSQL."""
    state_file = v3_path / "data" / "learning" / "learning_state.json"

    if not state_file.exists():
        logger.info("No learning state file found — skipping")
        return

    try:
        with open(state_file) as f:
            state = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"  Failed to read learning state: {e}")
        return

    logger.info(f"  Level: {state.get('level', 1)}, XP: {state.get('xp', 0)}")
    logger.info(f"  Insights: {len(state.get('insights', []))}")
    logger.info(f"  Learn calls: {state.get('total_learn_calls', 0)}")

    if dry_run:
        logger.info("  Would INSERT 1 row into learning_data table")
        logger.info(
            f"  Would INSERT {len(state.get('insights', []))} rows into insights table"
        )
        return

    # TODO: Implement actual migration
    # 1. Create learning_data row from state
    # 2. Create insight rows from state['insights']
    # 3. Create recommendation rows from state['recommendations']
    logger.info("  [STUB] Live migration not yet implemented")
