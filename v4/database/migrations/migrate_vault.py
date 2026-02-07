"""
Migrate V3 vault findings (JSONL) to V4 PostgreSQL.

V3 format: nps/data/findings/vault_live.jsonl
  Each line: {"address": "...", "chain": "btc", "balance": 0, "private_key": "ENC:...", ...}

V4 target: findings table
  - Decrypt ENC: values with V3 security module
  - Re-encrypt with AES-256-GCM
  - Generate UUIDs
  - Convert epoch timestamps to TIMESTAMPTZ
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def migrate_vault(v3_path: Path, dry_run: bool = True, v3_password: str = None):
    """Migrate V3 vault JSONL to V4 PostgreSQL findings table."""
    vault_file = v3_path / "data" / "findings" / "vault_live.jsonl"

    if not vault_file.exists():
        logger.info("No vault file found — skipping")
        return

    findings = []
    errors = 0

    with open(vault_file) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                findings.append(entry)
            except json.JSONDecodeError:
                errors += 1
                logger.warning(f"  Skipping corrupt line {line_num}")

    logger.info(
        f"  Found {len(findings)} vault records ({errors} corrupt lines skipped)"
    )

    if dry_run:
        # Preview
        encrypted_count = sum(
            1
            for f in findings
            if any(
                isinstance(f.get(k), str) and f[k].startswith("ENC:")
                for k in ["private_key", "seed_phrase", "wif", "extended_private_key"]
            )
        )
        logger.info(f"  {encrypted_count} records have encrypted fields")
        logger.info(f"  Would INSERT {len(findings)} rows into findings table")
        return

    # TODO: Implement actual migration
    # 1. Initialize V3 security module with v3_password
    # 2. For each finding:
    #    a. Decrypt ENC: fields with V3 decrypt()
    #    b. Re-encrypt with V4 AES-256-GCM
    #    c. Convert timestamp (epoch float) to datetime
    #    d. Generate UUID
    #    e. INSERT into findings table
    logger.info("  [STUB] Live migration not yet implemented")
