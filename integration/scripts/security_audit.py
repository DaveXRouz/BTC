#!/usr/bin/env python3
"""Security audit script for NPS V4 Oracle API.

Validates auth enforcement, input handling, credential hygiene, and CORS.

Usage:
    cd v4 && python3 integration/scripts/security_audit.py
"""

import os
import re
import sys
import time
from pathlib import Path

import requests

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "")

_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and key not in os.environ:
                os.environ[key] = value
    API_SECRET_KEY = os.environ.get("API_SECRET_KEY", API_SECRET_KEY)

V4_ROOT = Path(__file__).resolve().parents[2]

PROTECTED = [
    ("GET", "/api/oracle/users"),
    ("POST", "/api/oracle/users"),
    ("POST", "/api/oracle/reading"),
    ("POST", "/api/oracle/question"),
    ("POST", "/api/oracle/name"),
    ("GET", "/api/oracle/daily"),
    ("GET", "/api/oracle/readings"),
    ("GET", "/api/oracle/audit"),
]


def url(path):
    return f"{API_BASE_URL}{path}"


def check_api():
    try:
        return requests.get(url("/api/health"), timeout=5).status_code == 200
    except Exception:
        return False


def check_auth():
    """Protected endpoints must return 401 without credentials."""
    print("\n[1] Auth enforcement")
    issues = []
    for method, path in PROTECTED:
        r = requests.request(
            method, url(path), json={} if method == "POST" else None, timeout=5
        )
        ok = r.status_code == 401
        print(f"  {'PASS' if ok else 'FAIL'}: {method} {path} -> {r.status_code}")
        if not ok:
            issues.append(f"{method} {path}: got {r.status_code}")
    return issues


def check_bad_token():
    """Wrong token must return 401 or 403."""
    print("\n[2] Invalid token")
    issues = []
    h = {"Authorization": "Bearer wrong-value-here"}
    for method, path in PROTECTED[:3]:
        r = requests.request(
            method,
            url(path),
            json={} if method == "POST" else None,
            headers=h,
            timeout=5,
        )
        ok = r.status_code in (401, 403)
        print(f"  {'PASS' if ok else 'FAIL'}: {method} {path} -> {r.status_code}")
        if not ok:
            issues.append(f"{method} {path}: got {r.status_code}")
    return issues


def check_rate_limit():
    """Rapid requests should trigger 429 if configured."""
    print("\n[3] Rate limiting")
    h = {"Authorization": f"Bearer {API_SECRET_KEY}"}
    for i in range(100):
        r = requests.get(url("/api/oracle/users"), headers=h, timeout=2)
        if r.status_code == 429:
            print(f"  PASS: 429 after {i+1} requests")
            return []
    print("  INFO: No 429 (rate limiting may not be active)")
    return []


def check_input_handling():
    """Special characters in input fields must not cause errors."""
    print("\n[4] Input handling")
    s = requests.Session()
    s.headers.update(
        {
            "Authorization": f"Bearer {API_SECRET_KEY}",
            "Content-Type": "application/json",
        }
    )
    issues = []
    ids = []
    payloads = ["<b>bold</b>", "test'; --", "a" * 1000]
    for i, p in enumerate(payloads):
        r = s.post(
            url("/api/oracle/users"),
            json={
                "name": f"SecAudit_{i}_{int(time.time())}",
                "birthday": "1990-01-01",
                "mother_name": p,
            },
            timeout=10,
        )
        if r.status_code == 201:
            ids.append(r.json()["id"])
            print(f"  PASS: Input #{i+1} stored safely")
        elif r.status_code in (400, 422):
            print(f"  PASS: Input #{i+1} rejected")
        elif r.status_code == 500:
            issues.append(f"Input #{i+1} caused 500")
            print(f"  FAIL: Input #{i+1} caused 500")
        else:
            print(f"  INFO: Input #{i+1} -> {r.status_code}")
    for uid in ids:
        try:
            s.delete(url(f"/api/oracle/users/{uid}"))
        except Exception:
            pass
    return issues


def check_credentials_scan():
    """Scan source for leaked secret patterns."""
    print("\n[5] Credential scan")
    issues = []
    dirs = [V4_ROOT / "api", V4_ROOT / "frontend" / "src"]
    skip = {"node_modules", "__pycache__", ".git", "dist"}
    pats = [
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub token"),
        (r"(?:AKIA|AGPA)[A-Z0-9]{16}", "AWS key"),
    ]
    for d in dirs:
        if not d.exists():
            continue
        for ext in ("*.py", "*.ts", "*.tsx"):
            for f in d.rglob(ext):
                if any(s in str(f) for s in skip):
                    continue
                try:
                    c = f.read_text(errors="ignore")
                    for pat, desc in pats:
                        if re.search(pat, c):
                            issues.append(f"{desc} in {f.relative_to(V4_ROOT)}")
                            print(f"  FAIL: {desc} in {f.relative_to(V4_ROOT)}")
                except Exception:
                    pass
    if not issues:
        print("  PASS: No leaked credentials")
    return issues


def check_cors():
    """CORS must not allow arbitrary origins."""
    print("\n[6] CORS")
    issues = []
    h = {"Origin": "http://bad.example", "Authorization": f"Bearer {API_SECRET_KEY}"}
    r = requests.get(url("/api/oracle/users"), headers=h, timeout=5)
    acao = r.headers.get("Access-Control-Allow-Origin", "")
    if acao == "*" or "bad.example" in acao:
        issues.append("CORS wildcard")
        print("  FAIL: Allows any origin")
    else:
        print(f"  PASS: Origin restricted ('{acao}')")
    return issues


def check_no_subprocess():
    """No subprocess usage in production code."""
    print("\n[7] Subprocess scan")
    issues = []
    dirs = [V4_ROOT / "api", V4_ROOT / "services"]
    pats = [r"subprocess\.", r"os\.system\(", r"os\.popen\("]
    for d in dirs:
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            if "__pycache__" in str(f):
                continue
            try:
                c = f.read_text(errors="ignore")
                for p in pats:
                    if re.search(p, c):
                        rel = f.relative_to(V4_ROOT)
                        issues.append(f"subprocess in {rel}")
                        print(f"  FAIL: {rel}")
            except Exception:
                pass
    if not issues:
        print("  PASS: No subprocess calls")
    return issues


def main():
    print("=" * 60)
    print("NPS V4 Security Audit")
    print("=" * 60)
    if not check_api():
        print("ERROR: API not reachable")
        sys.exit(1)
    all_issues = []
    all_issues.extend(check_auth())
    all_issues.extend(check_bad_token())
    all_issues.extend(check_rate_limit())
    all_issues.extend(check_input_handling())
    all_issues.extend(check_credentials_scan())
    all_issues.extend(check_cors())
    all_issues.extend(check_no_subprocess())
    print("\n" + "=" * 60)
    if all_issues:
        print(f"ISSUES: {len(all_issues)}")
        for i in all_issues:
            print(f"  - {i}")
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
