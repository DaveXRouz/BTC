"""
NPS Legacy -> Current Data Migration Orchestrator

Migrates all legacy file-based data to current PostgreSQL.
Requires legacy master password for encrypted vault records.

Usage:
    python migrate_all.py --v3-path /path/to/nps --dry-run
    python migrate_all.py --v3-path /path/to/nps --execute
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def run_migration(v3_path: Path, dry_run: bool = True, v3_password: str = None):
    """Run all migration steps in order."""
    logger.info(
        f"NPS legacy -> current Migration {'(DRY RUN)' if dry_run else '(LIVE)'}"
    )
    logger.info(f"Legacy path: {v3_path}")

    # Validate legacy path
    if not (v3_path / "data").exists():
        logger.error(f"Legacy data directory not found at {v3_path / 'data'}")
        sys.exit(1)

    steps = [
        ("1. Migrate sessions", "migrate_sessions", "migrate_sessions"),
        ("2. Migrate vault findings", "migrate_vault", "migrate_vault"),
        ("3. Migrate learning data", "migrate_learning", "migrate_learning"),
        ("4. Migrate oracle readings", "migrate_readings", "migrate_readings"),
    ]

    for step_name, module_name, func_name in steps:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Step: {step_name}")
        logger.info(f"{'=' * 60}")

        # TODO: Import and call each migration module
        # module = importlib.import_module(module_name)
        # getattr(module, func_name)(v3_path, dry_run=dry_run, v3_password=v3_password)
        logger.info(f"  [STUB] {step_name} — not yet implemented")

    logger.info("\nMigration complete.")


def main():
    parser = argparse.ArgumentParser(description="NPS Legacy -> Current Data Migration")
    parser.add_argument(
        "--v3-path",
        type=Path,
        required=True,
        help="Path to legacy nps/ directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview changes without writing (default: True)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the migration",
    )
    parser.add_argument(
        "--v3-password",
        help="Legacy master password for decrypting ENC: vault records",
    )

    args = parser.parse_args()
    dry_run = not args.execute

    if not dry_run and not args.v3_password:
        logger.warning(
            "No legacy password provided. Encrypted vault records will be skipped."
        )

    run_migration(args.v3_path, dry_run=dry_run, v3_password=args.v3_password)


if __name__ == "__main__":
    main()
