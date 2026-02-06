"""
NPS V2 → V3 Data Migration
===========================
Run-once script to migrate V2 data files to V3 directory structure.
Originals are archived to data/v2_archive/.
"""

import json
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
ARCHIVE_DIR = DATA_DIR / "v2_archive"


def migrate():
    """Migrate V2 data to V3 structure. Safe to run multiple times."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    migrated = []

    # 1. scan_sessions.json → data/sessions/v2_sessions.json
    src = DATA_DIR / "scan_sessions.json"
    dst = DATA_DIR / "sessions" / "v2_sessions.json"
    if src.exists() and not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        shutil.move(str(src), str(ARCHIVE_DIR / "scan_sessions.json"))
        migrated.append("scan_sessions.json → sessions/v2_sessions.json")

    # 2. scanner_knowledge/ → data/learning/v2_knowledge/
    src_dir = DATA_DIR / "scanner_knowledge"
    dst_dir = DATA_DIR / "learning" / "v2_knowledge"
    if src_dir.exists() and src_dir.is_dir() and not dst_dir.exists():
        dst_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(str(src_dir), str(dst_dir))
        archive_dst = ARCHIVE_DIR / "scanner_knowledge"
        if not archive_dst.exists():
            shutil.move(str(src_dir), str(archive_dst))
        migrated.append("scanner_knowledge/ → learning/v2_knowledge/")

    # 3. scan_memory.json → data/learning/v2_memory.json
    src = DATA_DIR / "scan_memory.json"
    dst = DATA_DIR / "learning" / "v2_memory.json"
    if src.exists() and not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        shutil.move(str(src), str(ARCHIVE_DIR / "scan_memory.json"))
        migrated.append("scan_memory.json → learning/v2_memory.json")

    if migrated:
        logger.info("V2 → V3 migration complete: %s", ", ".join(migrated))
        print(f"Migrated {len(migrated)} items:")
        for m in migrated:
            print(f"  {m}")
    else:
        print("Nothing to migrate (already done or no V2 data found).")

    return migrated


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate()
