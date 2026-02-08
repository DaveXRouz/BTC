"""
Findings Vault — Encrypted persistent storage for NPS.

Append-only JSONL vault for wallet findings. Thread-safe writes, atomic
file operations, per-session tracking, and CSV/JSON export.

Reuses engines.security for encrypt_dict / decrypt_dict.
"""

import csv
import io
import json
import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
FINDINGS_DIR = DATA_DIR / "findings"
SESSIONS_DIR = FINDINGS_DIR / "sessions"
SUMMARIES_DIR = FINDINGS_DIR / "summaries"

_lock = threading.Lock()
_current_session = None
_session_count = 0
_total_findings = 0
_findings_since_summary = 0

SUMMARY_EVERY = 100


def init_vault():
    """Create vault directories if they don't exist."""
    for d in (FINDINGS_DIR, SESSIONS_DIR, SUMMARIES_DIR):
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Vault initialized")


def start_session(session_name=None):
    """Start a new vault session. Returns session_id."""
    global _current_session, _session_count
    ts = time.strftime("%Y%m%d_%H%M%S")
    name = session_name or "scan"
    session_id = f"{name}_{ts}"

    with _lock:
        _current_session = {
            "session_id": session_id,
            "name": session_name or "scan",
            "started": time.time(),
            "findings": 0,
        }
        _session_count += 1

    logger.info(f"Vault session started: {session_id}")
    return session_id


def record_finding(finding: dict) -> bool:
    """Record a finding to the vault. Thread-safe, encrypts sensitive fields.

    Args:
        finding: dict with keys like address, private_key, chain, balance, etc.

    Returns:
        True on success.
    """
    global _total_findings, _findings_since_summary

    if not isinstance(finding, dict):
        return False

    # Add metadata
    entry = dict(finding)
    entry["timestamp"] = time.time()
    entry["session"] = _current_session["session_id"] if _current_session else "unknown"

    # Encrypt sensitive fields
    try:
        from engines.security import encrypt_dict

        entry = encrypt_dict(entry)
    except ImportError:
        pass

    with _lock:
        # Append to live vault (JSONL)
        vault_path = FINDINGS_DIR / "vault_live.jsonl"
        try:
            with open(vault_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except IOError as e:
            logger.error(f"Failed to write finding: {e}")
            return False

        # Append to session file
        if _current_session:
            session_path = SESSIONS_DIR / f"{_current_session['session_id']}.jsonl"
            try:
                with open(session_path, "a") as f:
                    f.write(json.dumps(entry) + "\n")
            except IOError:
                pass
            _current_session["findings"] += 1

        _total_findings += 1
        _findings_since_summary += 1

        # Auto-summary every N findings
        if _findings_since_summary >= SUMMARY_EVERY:
            _write_summary_unlocked()
            _findings_since_summary = 0

    return True


def get_findings(decrypt_keys=False, limit=100) -> list:
    """Read findings from the vault. Optionally decrypt sensitive fields."""
    vault_path = FINDINGS_DIR / "vault_live.jsonl"
    if not vault_path.exists():
        return []

    findings = []
    try:
        with open(vault_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        findings.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except IOError:
        return []

    # Apply limit (most recent first)
    findings = findings[-limit:]

    if decrypt_keys:
        try:
            from engines.security import decrypt_dict

            findings = [decrypt_dict(f) for f in findings]
        except (ImportError, ValueError) as e:
            logger.warning(f"Could not decrypt findings: {e}")

    return findings


def get_summary() -> dict:
    """Return vault summary stats."""
    vault_path = FINDINGS_DIR / "vault_live.jsonl"

    total = 0
    with_balance = 0
    by_chain = {}
    vault_size = 0

    if vault_path.exists():
        vault_size = vault_path.stat().st_size
        try:
            with open(vault_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        total += 1
                        chain = entry.get("chain", "unknown")
                        by_chain[chain] = by_chain.get(chain, 0) + 1
                        bal = entry.get("balance", 0)
                        if isinstance(bal, (int, float)) and bal > 0:
                            with_balance += 1
                    except json.JSONDecodeError:
                        continue
        except IOError:
            pass

    return {
        "total": total,
        "with_balance": with_balance,
        "by_chain": by_chain,
        "vault_size": vault_size,
        "sessions": _session_count,
    }


def export_csv(output_path=None, decrypt_keys=False) -> str:
    """Export vault to CSV. Returns output path."""
    if output_path is None:
        output_path = str(FINDINGS_DIR / "vault_export.csv")

    findings = get_findings(decrypt_keys=decrypt_keys, limit=0)
    # limit=0 means we need all — override
    vault_path = FINDINGS_DIR / "vault_live.jsonl"
    if vault_path.exists():
        findings = []
        with open(vault_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        findings.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        if decrypt_keys:
            try:
                from engines.security import decrypt_dict

                findings = [decrypt_dict(f) for f in findings]
            except (ImportError, ValueError):
                pass

    if not findings:
        # Write empty CSV with headers
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "session", "chain", "address", "balance"])
        return output_path

    # Collect all unique keys
    all_keys = set()
    for f in findings:
        all_keys.update(f.keys())
    fieldnames = sorted(all_keys)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(findings)

    return output_path


def export_json(output_path=None, decrypt_keys=False) -> str:
    """Export vault to JSON. Returns output path."""
    if output_path is None:
        output_path = str(FINDINGS_DIR / "vault_export.json")

    vault_path = FINDINGS_DIR / "vault_live.jsonl"
    findings = []
    if vault_path.exists():
        with open(vault_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        findings.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    if decrypt_keys:
        try:
            from engines.security import decrypt_dict

            findings = [decrypt_dict(f) for f in findings]
        except (ImportError, ValueError):
            pass

    # Atomic write
    tmp_path = output_path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(findings, f, indent=2)
    os.replace(tmp_path, output_path)

    return output_path


def _write_summary_unlocked():
    """Write a summary file. Called with _lock held. Atomic write."""
    ts = time.strftime("%Y%m%d_%H%M%S")
    summary = get_summary()
    summary["generated_at"] = ts
    summary_path = SUMMARIES_DIR / f"summary_{ts}.json"
    try:
        tmp_path = summary_path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(summary, f, indent=2)
        os.replace(str(tmp_path), str(summary_path))
    except IOError as e:
        logger.error(f"Failed to write summary: {e}")


def shutdown():
    """Flush remaining data and create final summary."""
    with _lock:
        if _current_session:
            # Write session metadata
            session_meta = dict(_current_session)
            session_meta["ended"] = time.time()
            session_meta["duration"] = session_meta["ended"] - session_meta["started"]
            meta_path = SESSIONS_DIR / f"{_current_session['session_id']}_meta.json"
            try:
                with open(meta_path, "w") as f:
                    json.dump(session_meta, f, indent=2)
            except IOError:
                pass

        # Final summary
        _write_summary_unlocked()

    logger.info("Vault shutdown complete")
