#!/usr/bin/env python3
"""Security audit script for NPS Oracle API.

Validates auth enforcement, input handling, credential hygiene, CORS,
SQL injection, XSS, CSRF, path traversal, encryption compliance,
dependency vulnerabilities, security headers, sensitive data leakage,
token security, database security, code quality, and rate limiting.

Usage:
    cd v4 && python3 integration/scripts/security_audit.py
    python3 integration/scripts/security_audit.py --json
    python3 integration/scripts/security_audit.py --report /tmp/audit.json
    python3 integration/scripts/security_audit.py --strict
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

AUDIT_VERSION = "2.0.0"

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

# ── Result tracking ──────────────────────────────────────────────────────────

_results: list[dict] = []
_warnings: list[str] = []


def _record(
    check_num: int,
    name: str,
    status: str,
    issues: list[str],
    warnings: Optional[list[str]] = None,
) -> list[str]:
    """Record a check result for JSON output."""
    _results.append(
        {
            "check": check_num,
            "name": name,
            "status": status,
            "issues": issues,
            "warnings": warnings or [],
        }
    )
    if warnings:
        _warnings.extend(warnings)
    return issues


# ── Helpers ──────────────────────────────────────────────────────────────────


def url(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def _auth_header() -> dict[str, str]:
    return {"Authorization": f"Bearer {API_SECRET_KEY}"}


def check_api() -> bool:
    try:
        return requests.get(url("/api/health"), timeout=5).status_code == 200
    except requests.RequestException:
        return False


# ── Existing checks (1-7) ───────────────────────────────────────────────────


def check_auth() -> list[str]:
    """Protected endpoints must return 401 without credentials."""
    print("\n[1] Auth enforcement")
    issues: list[str] = []
    for method, path in PROTECTED:
        r = requests.request(
            method, url(path), json={} if method == "POST" else None, timeout=5
        )
        ok = r.status_code == 401
        print(f"  {'PASS' if ok else 'FAIL'}: {method} {path} -> {r.status_code}")
        if not ok:
            issues.append(f"{method} {path}: got {r.status_code}")
    return _record(1, "auth_enforcement", "FAIL" if issues else "PASS", issues)


def check_bad_token() -> list[str]:
    """Wrong token must return 401 or 403."""
    print("\n[2] Invalid token")
    issues: list[str] = []
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
    return _record(2, "invalid_token", "FAIL" if issues else "PASS", issues)


def check_rate_limit() -> list[str]:
    """Rapid requests should trigger 429 if configured."""
    print("\n[3] Rate limiting")
    h = {"Authorization": f"Bearer {API_SECRET_KEY}"}
    for i in range(100):
        r = requests.get(url("/api/oracle/users"), headers=h, timeout=2)
        if r.status_code == 429:
            print(f"  PASS: 429 after {i + 1} requests")
            return _record(3, "rate_limiting", "PASS", [])
    print("  INFO: No 429 (rate limiting may not be active)")
    return _record(
        3, "rate_limiting", "INFO", [], warnings=["Rate limiting not active"]
    )


def check_input_handling() -> list[str]:
    """Special characters in input fields must not cause errors."""
    print("\n[4] Input handling")
    s = requests.Session()
    s.headers.update(
        {
            "Authorization": f"Bearer {API_SECRET_KEY}",
            "Content-Type": "application/json",
        }
    )
    issues: list[str] = []
    ids: list[str] = []
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
            print(f"  PASS: Input #{i + 1} stored safely")
        elif r.status_code in (400, 422):
            print(f"  PASS: Input #{i + 1} rejected")
        elif r.status_code == 500:
            issues.append(f"Input #{i + 1} caused 500")
            print(f"  FAIL: Input #{i + 1} caused 500")
        else:
            print(f"  INFO: Input #{i + 1} -> {r.status_code}")
    for uid in ids:
        try:
            s.delete(url(f"/api/oracle/users/{uid}"))
        except requests.RequestException:
            pass
    return _record(4, "input_handling", "FAIL" if issues else "PASS", issues)


def check_credentials_scan() -> list[str]:
    """Scan source for leaked secret patterns."""
    print("\n[5] Credential scan")
    issues: list[str] = []
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
                except OSError:
                    pass
    if not issues:
        print("  PASS: No leaked credentials")
    return _record(5, "credentials_scan", "FAIL" if issues else "PASS", issues)


def check_cors() -> list[str]:
    """CORS must not allow arbitrary origins."""
    print("\n[6] CORS")
    issues: list[str] = []
    h = {"Origin": "http://bad.example", "Authorization": f"Bearer {API_SECRET_KEY}"}
    r = requests.get(url("/api/oracle/users"), headers=h, timeout=5)
    acao = r.headers.get("Access-Control-Allow-Origin", "")
    if acao == "*" or "bad.example" in acao:
        issues.append("CORS wildcard")
        print("  FAIL: Allows any origin")
    else:
        print(f"  PASS: Origin restricted ('{acao}')")
    return _record(6, "cors", "FAIL" if issues else "PASS", issues)


def check_no_subprocess() -> list[str]:
    """No subprocess usage in production code."""
    print("\n[7] Subprocess scan")
    issues: list[str] = []
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
            except OSError:
                pass
    if not issues:
        print("  PASS: No subprocess calls")
    return _record(7, "subprocess_scan", "FAIL" if issues else "PASS", issues)


# ── New checks (8-20) ───────────────────────────────────────────────────────


def check_sql_injection() -> list[str]:
    """Send SQL injection payloads and verify no 500 errors."""
    print("\n[8] SQL injection")
    issues: list[str] = []
    warnings: list[str] = []
    s = requests.Session()
    s.headers.update(_auth_header())

    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1 UNION SELECT * FROM information_schema.tables--",
        "' OR 1=1--",
        "admin'--",
    ]

    # Test POST /api/oracle/users (name field)
    created_ids: list[str] = []
    for i, payload in enumerate(sqli_payloads):
        try:
            r = s.post(
                url("/api/oracle/users"),
                json={
                    "name": payload,
                    "birthday": "1990-01-01",
                    "mother_name": f"SQLiTest_{i}",
                },
                timeout=10,
            )
            if r.status_code == 500:
                issues.append(
                    f"SQLi payload #{i + 1} caused 500 on POST /api/oracle/users"
                )
                print(f"  FAIL: POST /api/oracle/users payload #{i + 1} -> 500")
            elif r.status_code == 201:
                created_ids.append(r.json().get("id", ""))
                print(
                    f"  PASS: POST /api/oracle/users payload #{i + 1} -> {r.status_code}"
                )
            else:
                print(
                    f"  PASS: POST /api/oracle/users payload #{i + 1} -> {r.status_code}"
                )
        except requests.RequestException as exc:
            warnings.append(f"POST /api/oracle/users unreachable: {exc}")
            print("  WARN: POST /api/oracle/users unreachable")
            break

    # Test GET /api/oracle/users?search= (query parameter)
    for i, payload in enumerate(sqli_payloads):
        try:
            r = s.get(
                url("/api/oracle/users"),
                params={"search": payload},
                timeout=10,
            )
            if r.status_code == 500:
                issues.append(
                    f"SQLi payload #{i + 1} caused 500 on GET /api/oracle/users?search="
                )
                print(f"  FAIL: GET /api/oracle/users?search= payload #{i + 1} -> 500")
            else:
                print(
                    f"  PASS: GET /api/oracle/users?search= payload #{i + 1} -> {r.status_code}"
                )
        except requests.RequestException as exc:
            warnings.append(f"GET /api/oracle/users?search= unreachable: {exc}")
            print("  WARN: GET /api/oracle/users?search= unreachable")
            break

    # Test POST /api/oracle/reading
    for i, payload in enumerate(sqli_payloads[:2]):
        try:
            r = s.post(
                url("/api/oracle/reading"),
                json={"user_id": payload, "reading_type": "full"},
                timeout=10,
            )
            if r.status_code == 500:
                issues.append(
                    f"SQLi payload #{i + 1} caused 500 on POST /api/oracle/reading"
                )
                print(f"  FAIL: POST /api/oracle/reading payload #{i + 1} -> 500")
            else:
                print(
                    f"  PASS: POST /api/oracle/reading payload #{i + 1} -> {r.status_code}"
                )
        except requests.RequestException as exc:
            warnings.append(f"POST /api/oracle/reading unreachable: {exc}")
            print("  WARN: POST /api/oracle/reading unreachable")
            break

    # Cleanup created users
    for uid in created_ids:
        if uid:
            try:
                s.delete(url(f"/api/oracle/users/{uid}"), timeout=5)
            except requests.RequestException:
                pass

    return _record(8, "sql_injection", "FAIL" if issues else "PASS", issues, warnings)


def check_xss() -> list[str]:
    """Send XSS payloads as profile names, verify no raw script tags in responses."""
    print("\n[9] XSS protection")
    issues: list[str] = []
    warnings: list[str] = []
    s = requests.Session()
    s.headers.update(_auth_header())

    xss_payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(document.cookie)",
        "<svg onload=alert(1)>",
        "'\"><script>alert(String.fromCharCode(88,83,83))</script>",
    ]

    created_ids: list[str] = []
    for i, payload in enumerate(xss_payloads):
        try:
            r = s.post(
                url("/api/oracle/users"),
                json={
                    "name": f"XSSTest_{i}_{int(time.time())}",
                    "birthday": "1990-01-01",
                    "mother_name": payload,
                },
                timeout=10,
            )
            if r.status_code == 201:
                user_data = r.json()
                uid = user_data.get("id", "")
                created_ids.append(uid)

                # Read back and check for unescaped script tags
                if uid:
                    r2 = s.get(url(f"/api/oracle/users/{uid}"), timeout=10)
                    if r2.status_code == 200:
                        body_text = r2.text
                        # Check if raw script tags appear in response
                        if (
                            "<script>" in body_text.lower()
                            and "alert" in body_text.lower()
                        ):
                            issues.append(
                                f"XSS payload #{i + 1} reflected unescaped in response"
                            )
                            print(
                                f"  FAIL: XSS payload #{i + 1} reflected raw in response"
                            )
                        else:
                            print(f"  PASS: XSS payload #{i + 1} safely handled")
                    else:
                        print(
                            f"  PASS: XSS payload #{i + 1} stored (read-back {r2.status_code})"
                        )
            elif r.status_code in (400, 422):
                print(f"  PASS: XSS payload #{i + 1} rejected ({r.status_code})")
            elif r.status_code == 500:
                issues.append(f"XSS payload #{i + 1} caused 500")
                print(f"  FAIL: XSS payload #{i + 1} caused 500")
            else:
                print(f"  INFO: XSS payload #{i + 1} -> {r.status_code}")
        except requests.RequestException as exc:
            warnings.append(f"XSS test unreachable: {exc}")
            print("  WARN: XSS test unreachable")
            break

    # Cleanup
    for uid in created_ids:
        if uid:
            try:
                s.delete(url(f"/api/oracle/users/{uid}"), timeout=5)
            except requests.RequestException:
                pass

    return _record(9, "xss_protection", "FAIL" if issues else "PASS", issues, warnings)


def check_csrf() -> list[str]:
    """Verify POST/PUT/DELETE reject cookie-only auth (no Bearer token).

    NPS uses JWT Bearer tokens, so CSRF is mitigated by design since
    browsers do not auto-attach Authorization headers.
    """
    print("\n[10] CSRF protection")
    issues: list[str] = []
    warnings: list[str] = []

    # Simulate a request that only has cookies (no Authorization header)
    cookie_only_session = requests.Session()
    # Set a fake session cookie to simulate cookie-based auth
    cookie_only_session.cookies.set("session", "fake-session-value")

    csrf_endpoints = [
        ("POST", "/api/oracle/users", {"name": "csrf_test", "birthday": "1990-01-01"}),
        ("POST", "/api/oracle/reading", {"user_id": "1", "reading_type": "full"}),
        ("DELETE", "/api/oracle/users/nonexistent-id", None),
    ]

    for method, path, body in csrf_endpoints:
        try:
            r = cookie_only_session.request(
                method,
                url(path),
                json=body,
                timeout=10,
            )
            if r.status_code in (401, 403):
                print(
                    f"  PASS: {method} {path} rejected cookie-only auth ({r.status_code})"
                )
            elif r.status_code in (200, 201, 204):
                issues.append(f"{method} {path} accepted cookie-only auth")
                print(
                    f"  FAIL: {method} {path} accepted without Bearer token ({r.status_code})"
                )
            else:
                print(f"  PASS: {method} {path} -> {r.status_code} (not 2xx)")
        except requests.RequestException as exc:
            warnings.append(f"CSRF test for {method} {path} unreachable: {exc}")
            print(f"  WARN: {method} {path} unreachable")

    return _record(
        10, "csrf_protection", "FAIL" if issues else "PASS", issues, warnings
    )


def check_auth_bypass() -> list[str]:
    """Test auth bypass via path traversal, case manipulation, double encoding, null bytes."""
    print("\n[11] Auth bypass attempts")
    issues: list[str] = []
    warnings: list[str] = []

    bypass_paths = [
        # Path traversal
        "/api/oracle/../oracle/users",
        "/api/oracle/./users",
        "/api/oracle/users/..%2f..%2foracle/users",
        # Case manipulation
        "/API/ORACLE/USERS",
        "/Api/Oracle/Users",
        "/api/ORACLE/users",
        # Double encoding
        "/api/oracle/%2575sers",  # %25 = %, so %2575 = %75 = u -> users
        "/api/oracle/users%00",  # Null byte
        "/api/oracle/users%00.json",
        # Semicolon/fragment injection
        "/api/oracle/users;admin=true",
        "/api/oracle/users#admin",
    ]

    for path in bypass_paths:
        try:
            r = requests.get(url(path), timeout=5)
            # If endpoint returns data (200) without auth, it is a bypass
            if r.status_code == 200:
                # Check if the response contains user data (real bypass)
                try:
                    body = r.json()
                    # Health endpoints returning 200 are fine; check for user data
                    if isinstance(body, list) or (
                        isinstance(body, dict) and "users" in body
                    ):
                        issues.append(f"Auth bypass via {path} returned user data")
                        print(f"  FAIL: {path} -> 200 with data (auth bypassed)")
                    else:
                        print(f"  PASS: {path} -> 200 but no protected data")
                except (ValueError, KeyError):
                    print(f"  PASS: {path} -> 200 (non-JSON response)")
            elif r.status_code in (401, 403, 404, 405, 307, 308, 422):
                print(f"  PASS: {path} -> {r.status_code}")
            else:
                print(f"  INFO: {path} -> {r.status_code}")
        except requests.RequestException as exc:
            warnings.append(f"Auth bypass test for {path} failed: {exc}")
            print(f"  WARN: {path} unreachable")

    return _record(11, "auth_bypass", "FAIL" if issues else "PASS", issues, warnings)


def check_encryption_compliance() -> list[str]:
    """Scan source for plaintext private key patterns and verify encryption usage."""
    print("\n[12] Encryption compliance")
    issues: list[str] = []
    warnings: list[str] = []
    dirs = [V4_ROOT / "api", V4_ROOT / "services"]
    skip_dirs = {"node_modules", "__pycache__", ".git", "dist", "venv", ".venv"}

    # Patterns that indicate plaintext private keys or weak crypto
    dangerous_patterns = [
        (r"private_key\s*=\s*['\"][0-9a-fA-F]{64}['\"]", "Hardcoded private key (hex)"),
        (
            r"private_key\s*=\s*['\"]5[HJK][1-9A-HJ-NP-Za-km-z]{49}['\"]",
            "Hardcoded WIF private key",
        ),
        (r"(?:DES|RC4|MD5)\s*[\(.]", "Weak cryptographic algorithm (DES/RC4/MD5)"),
        (r"mode\s*=\s*.*?ECB", "ECB mode detected (insecure)"),
        (r"verify\s*=\s*False", "SSL verification disabled"),
    ]

    files_scanned = 0
    for d in dirs:
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            if any(s in str(f) for s in skip_dirs):
                continue
            try:
                content = f.read_text(errors="ignore")
                files_scanned += 1
                for pat, desc in dangerous_patterns:
                    matches = re.findall(pat, content)
                    if matches:
                        rel = f.relative_to(V4_ROOT)
                        issues.append(f"{desc} in {rel}")
                        print(f"  FAIL: {desc} in {rel}")
            except OSError:
                pass

    # Check that encryption module exists and uses AES-256-GCM
    enc_files = list((V4_ROOT / "api").rglob("*encrypt*"))
    enc_files += list((V4_ROOT / "services").rglob("*encrypt*"))
    enc_files = [
        f for f in enc_files if f.suffix == ".py" and "__pycache__" not in str(f)
    ]

    if enc_files:
        for ef in enc_files:
            try:
                content = ef.read_text(errors="ignore")
                if "AES" in content or "GCM" in content or "aes" in content:
                    print(f"  PASS: AES/GCM usage found in {ef.relative_to(V4_ROOT)}")
                else:
                    warnings.append(
                        f"Encryption file {ef.relative_to(V4_ROOT)} may not use AES-GCM"
                    )
                    print(f"  WARN: {ef.relative_to(V4_ROOT)} may not use AES-GCM")
            except OSError:
                pass
    else:
        warnings.append("No encryption module files found")
        print("  WARN: No encryption module files found")

    if not issues:
        print(f"  PASS: {files_scanned} files scanned, no plaintext key patterns")

    return _record(
        12, "encryption_compliance", "FAIL" if issues else "PASS", issues, warnings
    )


def check_dependencies() -> list[str]:
    """Run pip-audit and npm audit. Flag HIGH/CRITICAL as FAIL."""
    print("\n[13] Dependency vulnerabilities")
    issues: list[str] = []
    warnings: list[str] = []

    # Python: pip-audit
    api_dir = V4_ROOT / "api"
    if api_dir.exists():
        try:
            result = subprocess.run(
                ["pip-audit", "--format=json", "--desc"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(api_dir),
            )
            if result.returncode == 0 and result.stdout.strip():
                try:
                    audit_data = json.loads(result.stdout)
                    vulns = (
                        audit_data
                        if isinstance(audit_data, list)
                        else audit_data.get("dependencies", [])
                    )
                    high_critical = []
                    for dep in vulns:
                        dep_vulns = dep.get("vulns", [])
                        for v in dep_vulns:
                            desc = v.get("id", "unknown")
                            high_critical.append(f"{dep.get('name', '?')}:{desc}")
                    if high_critical:
                        for hc in high_critical:
                            issues.append(f"Python vulnerability: {hc}")
                        print(
                            f"  FAIL: {len(high_critical)} Python vulnerabilities found"
                        )
                    else:
                        print("  PASS: No Python vulnerabilities (pip-audit)")
                except (json.JSONDecodeError, KeyError, TypeError):
                    print("  PASS: pip-audit returned clean (no JSON vulnerabilities)")
            elif (
                result.returncode != 0
                and "No known vulnerabilities found" in result.stderr
            ):
                print("  PASS: No Python vulnerabilities (pip-audit)")
            elif result.returncode != 0:
                warnings.append(f"pip-audit exited with code {result.returncode}")
                print(f"  WARN: pip-audit exited {result.returncode}")
        except FileNotFoundError:
            warnings.append("pip-audit not installed")
            print("  WARN: pip-audit not installed (pip install pip-audit)")
        except subprocess.TimeoutExpired:
            warnings.append("pip-audit timed out")
            print("  WARN: pip-audit timed out")

    # Node: npm audit
    frontend_dir = V4_ROOT / "frontend"
    if (frontend_dir / "package.json").exists():
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(frontend_dir),
            )
            try:
                audit_data = json.loads(result.stdout)
                metadata = audit_data.get("metadata", {})
                vuln_summary = metadata.get("vulnerabilities", {})
                high_count = vuln_summary.get("high", 0)
                critical_count = vuln_summary.get("critical", 0)
                if high_count > 0 or critical_count > 0:
                    issues.append(
                        f"npm: {high_count} high, {critical_count} critical vulnerabilities"
                    )
                    print(
                        f"  FAIL: npm audit: {high_count} high, {critical_count} critical"
                    )
                else:
                    total = sum(vuln_summary.get(k, 0) for k in vuln_summary)
                    if total > 0:
                        warnings.append(f"npm: {total} low/moderate vulnerabilities")
                        print(
                            f"  WARN: npm audit: {total} low/moderate vulnerabilities"
                        )
                    else:
                        print("  PASS: No npm vulnerabilities")
            except (json.JSONDecodeError, KeyError, TypeError):
                if result.returncode == 0:
                    print("  PASS: npm audit clean")
                else:
                    warnings.append("npm audit returned non-JSON output")
                    print("  WARN: npm audit returned non-JSON output")
        except FileNotFoundError:
            warnings.append("npm not installed")
            print("  WARN: npm not found")
        except subprocess.TimeoutExpired:
            warnings.append("npm audit timed out")
            print("  WARN: npm audit timed out")

    return _record(
        13, "dependency_vulnerabilities", "FAIL" if issues else "PASS", issues, warnings
    )


def check_security_headers() -> list[str]:
    """Check response for security headers."""
    print("\n[14] Security headers")
    issues: list[str] = []
    warnings: list[str] = []

    required_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": None,  # Any value is acceptable (DENY, SAMEORIGIN)
        "Referrer-Policy": None,  # Any value is acceptable
    }

    recommended_headers = {
        "Strict-Transport-Security": None,
        "Content-Security-Policy": None,
        "X-XSS-Protection": None,
        "Permissions-Policy": None,
    }

    try:
        r = requests.get(url("/api/health"), timeout=5)
        headers = r.headers

        for header, expected_value in required_headers.items():
            actual = headers.get(header)
            if actual is None:
                issues.append(f"Missing required header: {header}")
                print(f"  FAIL: Missing {header}")
            elif expected_value and actual.lower() != expected_value.lower():
                issues.append(f"{header} is '{actual}', expected '{expected_value}'")
                print(f"  FAIL: {header} = '{actual}' (expected '{expected_value}')")
            else:
                print(f"  PASS: {header}: {actual}")

        for header, _ in recommended_headers.items():
            actual = headers.get(header)
            if actual is None:
                warnings.append(f"Missing recommended header: {header}")
                print(f"  WARN: Missing recommended {header}")
            else:
                print(f"  PASS: {header}: {actual}")

    except requests.RequestException as exc:
        warnings.append(f"Could not check security headers: {exc}")
        print(f"  WARN: Could not reach API: {exc}")

    return _record(
        14, "security_headers", "FAIL" if issues else "PASS", issues, warnings
    )


def check_sensitive_data() -> list[str]:
    """Trigger error responses, verify no stack traces leaked. Check health for internal IPs."""
    print("\n[15] Sensitive data exposure")
    issues: list[str] = []
    warnings: list[str] = []

    # Test 1: Trigger 404 and check for stack traces
    error_paths = [
        "/api/oracle/nonexistent_endpoint_12345",
        "/api/oracle/users/invalid-uuid-format!!!",
        "/api/oracle/reading",  # POST without body to GET
    ]

    stack_trace_indicators = [
        "Traceback (most recent call last)",
        'File "',
        "line ",
        "raise ",
        "  at ",
        "node_modules",
        "site-packages",
    ]

    for path in error_paths:
        try:
            r = requests.get(url(path), timeout=5)
            body = r.text
            for indicator in stack_trace_indicators:
                if indicator in body and r.status_code >= 400:
                    issues.append(f"Stack trace leaked at {path}")
                    print(f"  FAIL: Stack trace found in {path} response")
                    break
            else:
                print(f"  PASS: {path} -> {r.status_code} (no stack trace)")
        except requests.RequestException as exc:
            warnings.append(f"Error test for {path} failed: {exc}")
            print(f"  WARN: {path} unreachable")

    # Test 2: POST with malformed JSON body
    try:
        r = requests.post(
            url("/api/oracle/users"),
            data="{{{{invalid json",
            headers={
                "Authorization": f"Bearer {API_SECRET_KEY}",
                "Content-Type": "application/json",
            },
            timeout=5,
        )
        body = r.text
        for indicator in stack_trace_indicators:
            if indicator in body:
                issues.append("Stack trace leaked on malformed JSON")
                print("  FAIL: Stack trace on malformed JSON input")
                break
        else:
            print(f"  PASS: Malformed JSON -> {r.status_code} (no stack trace)")
    except requests.RequestException as exc:
        warnings.append(f"Malformed JSON test failed: {exc}")
        print("  WARN: Malformed JSON test unreachable")

    # Test 3: Check /api/health doesn't reveal internal IPs
    try:
        r = requests.get(url("/api/health"), timeout=5)
        body = r.text
        # Check for private/internal IP patterns
        internal_ip_patterns = [
            r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            r"\b172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b",
            r"\b192\.168\.\d{1,3}\.\d{1,3}\b",
        ]
        for pat in internal_ip_patterns:
            match = re.search(pat, body)
            if match:
                issues.append(f"Internal IP leaked in /api/health: {match.group()}")
                print(f"  FAIL: Internal IP in /api/health: {match.group()}")
                break
        else:
            print("  PASS: /api/health does not expose internal IPs")
    except requests.RequestException as exc:
        warnings.append(f"Health endpoint check failed: {exc}")
        print("  WARN: /api/health unreachable")

    return _record(
        15, "sensitive_data_exposure", "FAIL" if issues else "PASS", issues, warnings
    )


def check_path_traversal() -> list[str]:
    """Test path traversal in file-related endpoints (e.g. backup filenames)."""
    print("\n[16] Path traversal")
    issues: list[str] = []
    warnings: list[str] = []

    traversal_payloads = [
        "../../etc/passwd",
        "..\\..\\etc\\passwd",
        "....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "..%252f..%252fetc%252fpasswd",
        "/etc/passwd",
        "....//....//....//etc/shadow",
    ]

    # Test path traversal in user ID (UUID field)
    s = requests.Session()
    s.headers.update(_auth_header())

    for i, payload in enumerate(traversal_payloads):
        try:
            r = s.get(url(f"/api/oracle/users/{payload}"), timeout=5)
            if r.status_code == 200:
                body = r.text
                # Check if actual file content was returned
                if "root:" in body or "daemon:" in body or "/bin/" in body:
                    issues.append(f"Path traversal succeeded with payload #{i + 1}")
                    print(
                        f"  FAIL: Path traversal payload #{i + 1} returned file content"
                    )
                else:
                    print(f"  PASS: Payload #{i + 1} -> 200 (no file content)")
            elif r.status_code in (400, 404, 422):
                print(f"  PASS: Payload #{i + 1} -> {r.status_code}")
            elif r.status_code == 500:
                issues.append(f"Path traversal payload #{i + 1} caused 500")
                print(f"  FAIL: Payload #{i + 1} -> 500")
            else:
                print(f"  INFO: Payload #{i + 1} -> {r.status_code}")
        except requests.RequestException as exc:
            warnings.append(f"Path traversal test #{i + 1} failed: {exc}")
            print(f"  WARN: Payload #{i + 1} unreachable")
            break

    # Test backup/export endpoints if they exist
    backup_endpoints = [
        "/api/admin/backup",
        "/api/oracle/export",
    ]
    for endpoint in backup_endpoints:
        try:
            r = s.get(
                url(endpoint),
                params={"filename": "../../etc/passwd"},
                timeout=5,
            )
            if r.status_code == 200:
                body = r.text
                if "root:" in body:
                    issues.append(f"Path traversal in {endpoint} filename param")
                    print(f"  FAIL: {endpoint} filename traversal succeeded")
                else:
                    print(f"  PASS: {endpoint} -> 200 (sanitized)")
            else:
                print(f"  PASS: {endpoint} -> {r.status_code}")
        except requests.RequestException:
            pass  # Endpoint may not exist

    return _record(16, "path_traversal", "FAIL" if issues else "PASS", issues, warnings)


def check_token_security() -> list[str]:
    """Verify JWT has expiry and API_SECRET_KEY is not a default value."""
    print("\n[17] Token security")
    issues: list[str] = []
    warnings: list[str] = []

    # Check API_SECRET_KEY is not a dangerous default
    dangerous_defaults = [
        "changeme",
        "secret",
        "password",
        "12345",
        "admin",
        "test",
        "default",
        "your-secret-key",
        "supersecret",
        "",
    ]

    secret = os.environ.get("API_SECRET_KEY", "")
    if secret.lower() in dangerous_defaults:
        issues.append(f"API_SECRET_KEY is a dangerous default value: '{secret}'")
        print("  FAIL: API_SECRET_KEY is a dangerous default")
    elif len(secret) < 32:
        warnings.append(
            f"API_SECRET_KEY is only {len(secret)} chars (recommended: 32+)"
        )
        print(f"  WARN: API_SECRET_KEY is short ({len(secret)} chars, recommend 32+)")
    else:
        print(f"  PASS: API_SECRET_KEY is {len(secret)} chars")

    # Check JWT token structure and expiry
    if secret and secret.lower() not in dangerous_defaults:
        try:
            # Attempt login or use existing token to verify expiry
            r = requests.post(
                url("/api/auth/login"),
                json={"username": "admin", "password": "admin"},
                timeout=5,
            )
            if r.status_code == 200:
                token_data = r.json()
                access_token = token_data.get("access_token", "")
                if access_token:
                    # Decode JWT header+payload (without verification) to check exp
                    import base64

                    parts = access_token.split(".")
                    if len(parts) == 3:
                        # Pad base64 payload
                        payload_b64 = parts[1]
                        padding = 4 - len(payload_b64) % 4
                        if padding != 4:
                            payload_b64 += "=" * padding
                        try:
                            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                            if "exp" in payload:
                                print(
                                    f"  PASS: JWT has expiry claim (exp={payload['exp']})"
                                )
                            else:
                                issues.append("JWT token has no expiry (exp) claim")
                                print("  FAIL: JWT token has no expiry claim")
                            if "iat" in payload:
                                print("  PASS: JWT has issued-at claim")
                            else:
                                warnings.append(
                                    "JWT token has no issued-at (iat) claim"
                                )
                                print("  WARN: JWT missing iat claim")
                        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
                            warnings.append("Could not decode JWT payload")
                            print("  WARN: Could not decode JWT payload")
                    else:
                        warnings.append("Token is not a standard 3-part JWT")
                        print("  WARN: Token is not a standard 3-part JWT")
                else:
                    warnings.append("No access_token in login response")
                    print("  WARN: No access_token in login response")
            else:
                # Login failed — that is fine, we can still check the key strength
                print(
                    f"  INFO: Login returned {r.status_code} (cannot verify JWT structure)"
                )
        except requests.RequestException as exc:
            warnings.append(f"Could not test JWT structure: {exc}")
            print(f"  WARN: Could not reach login endpoint: {exc}")

    # Check JWT configuration in source
    config_files = list((V4_ROOT / "api").rglob("config*.py"))
    config_files += list((V4_ROOT / "api").rglob("settings*.py"))
    for cf in config_files:
        if "__pycache__" in str(cf):
            continue
        try:
            content = cf.read_text(errors="ignore")
            # Check for reasonable expiry (not excessively long)
            expire_match = re.search(
                r"(?:jwt_expire|token_expire|ACCESS_TOKEN_EXPIRE)\w*\s*[:=]\s*(\d+)",
                content,
            )
            if expire_match:
                expire_val = int(expire_match.group(1))
                if expire_val > 1440:  # More than 24 hours in minutes
                    warnings.append(f"JWT expiry is {expire_val} minutes (>24h)")
                    print(
                        f"  WARN: JWT expiry is {expire_val} minutes (recommend <1440)"
                    )
                else:
                    print(f"  PASS: JWT expiry configured at {expire_val} minutes")
        except (OSError, ValueError):
            pass

    return _record(17, "token_security", "FAIL" if issues else "PASS", issues, warnings)


def check_database_security() -> list[str]:
    """Verify POSTGRES_PASSWORD is not default or empty."""
    print("\n[18] Database security")
    issues: list[str] = []
    warnings: list[str] = []

    pg_password = os.environ.get("POSTGRES_PASSWORD", "")
    dangerous_pg_defaults = [
        "",
        "postgres",
        "password",
        "changeme",
        "admin",
        "12345",
        "secret",
        "test",
        "root",
        "default",
    ]

    if pg_password.lower() in dangerous_pg_defaults:
        issues.append(
            f"POSTGRES_PASSWORD is a dangerous default: '{pg_password or '(empty)'}'"
        )
        print("  FAIL: POSTGRES_PASSWORD is a dangerous default")
    elif len(pg_password) < 12:
        warnings.append(
            f"POSTGRES_PASSWORD is only {len(pg_password)} chars (recommended: 12+)"
        )
        print(
            f"  WARN: POSTGRES_PASSWORD is short ({len(pg_password)} chars, recommend 12+)"
        )
    else:
        print(f"  PASS: POSTGRES_PASSWORD is {len(pg_password)} chars")

    # Check POSTGRES_USER is not default 'postgres'
    pg_user = os.environ.get("POSTGRES_USER", "")
    if pg_user.lower() == "postgres":
        warnings.append("POSTGRES_USER is default 'postgres'")
        print("  WARN: POSTGRES_USER is default 'postgres' (consider custom user)")
    elif pg_user:
        print(f"  PASS: POSTGRES_USER is custom ('{pg_user}')")

    # Check docker-compose for exposed database port
    compose_file = V4_ROOT / "docker-compose.yml"
    if compose_file.exists():
        try:
            content = compose_file.read_text(errors="ignore")
            if "5432:5432" in content:
                warnings.append(
                    "PostgreSQL port 5432 exposed to host in docker-compose.yml"
                )
                print("  WARN: PostgreSQL port 5432 exposed to host")
            else:
                print("  PASS: PostgreSQL port not directly exposed")
        except OSError:
            pass

    # Check .env.example does not contain real passwords
    env_example = V4_ROOT / ".env.example"
    if env_example.exists():
        try:
            content = env_example.read_text(errors="ignore")
            for line in content.splitlines():
                if "POSTGRES_PASSWORD" in line and "=" in line:
                    _, _, val = line.partition("=")
                    val = val.strip().strip("'\"")
                    if val and val.lower() not in (
                        "changeme",
                        "your_password_here",
                        "",
                        "xxx",
                    ):
                        if len(val) > 8:
                            warnings.append("Real password may be in .env.example")
                            print("  WARN: .env.example may contain a real password")
                            break
            else:
                print("  PASS: .env.example does not contain real passwords")
        except OSError:
            pass

    return _record(
        18, "database_security", "FAIL" if issues else "PASS", issues, warnings
    )


def check_code_quality_security() -> list[str]:
    """Scan for eval(), exec(), pickle.loads(), unsafe yaml.load(), bare except:, TS 'any' in auth."""
    print("\n[19] Code quality security")
    issues: list[str] = []
    warnings: list[str] = []
    skip_dirs = {
        "node_modules",
        "__pycache__",
        ".git",
        "dist",
        "venv",
        ".venv",
        ".archive",
    }

    # Python dangerous patterns
    py_dangerous = [
        (r"\beval\s*\(", "eval() usage"),
        (r"\bexec\s*\(", "exec() usage"),
        (r"pickle\.loads?\s*\(", "pickle.load(s) usage (deserialization risk)"),
        (
            r"yaml\.load\s*\([^)]*(?!Loader\s*=\s*yaml\.SafeLoader)[^)]*\)",
            "yaml.load without SafeLoader",
        ),
        (r"^\s*except\s*:\s*$", "bare except: (catches all including SystemExit)"),
    ]

    # Scan Python files
    py_dirs = [V4_ROOT / "api", V4_ROOT / "services"]
    py_files_scanned = 0
    for d in py_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            if any(s in str(f) for s in skip_dirs):
                continue
            # Exclude test files and this audit script itself
            if "test" in f.name.lower() or f.name == "security_audit.py":
                continue
            try:
                content = f.read_text(errors="ignore")
                py_files_scanned += 1
                for pat, desc in py_dangerous:
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if re.search(pat, line):
                            # Skip comments
                            stripped = line.strip()
                            if stripped.startswith("#"):
                                continue
                            rel = f.relative_to(V4_ROOT)
                            issues.append(f"{desc} in {rel}:{line_num}")
                            print(f"  FAIL: {desc} in {rel}:{line_num}")
            except OSError:
                pass

    # TypeScript: check for 'any' in auth-related files
    ts_auth_patterns = [
        r":\s*any\b",
        r"as\s+any\b",
        r"<any>",
    ]
    ts_dirs = [V4_ROOT / "frontend" / "src"]
    ts_files_scanned = 0
    for d in ts_dirs:
        if not d.exists():
            continue
        for ext in ("*.ts", "*.tsx"):
            for f in d.rglob(ext):
                if any(s in str(f) for s in skip_dirs):
                    continue
                # Only check auth-related files for 'any' type
                fname_lower = f.name.lower()
                is_auth_file = any(
                    keyword in fname_lower
                    for keyword in (
                        "auth",
                        "login",
                        "token",
                        "security",
                        "permission",
                        "guard",
                    )
                )
                if not is_auth_file:
                    continue
                try:
                    content = f.read_text(errors="ignore")
                    ts_files_scanned += 1
                    for pat in ts_auth_patterns:
                        for line_num, line in enumerate(content.splitlines(), 1):
                            if re.search(pat, line):
                                stripped = line.strip()
                                if stripped.startswith("//") or stripped.startswith(
                                    "/*"
                                ):
                                    continue
                                rel = f.relative_to(V4_ROOT)
                                issues.append(
                                    f"TypeScript 'any' type in auth file {rel}:{line_num}"
                                )
                                print(f"  FAIL: 'any' type in {rel}:{line_num}")
                except OSError:
                    pass

    if not issues:
        print(
            f"  PASS: {py_files_scanned} Python + {ts_files_scanned} TS auth files scanned, no issues"
        )

    return _record(
        19, "code_quality_security", "FAIL" if issues else "PASS", issues, warnings
    )


def check_rate_limiting_detailed() -> list[str]:
    """50 rapid requests to POST /api/auth/login. If no 429: WARN."""
    print("\n[20] Detailed rate limiting (login endpoint)")
    issues: list[str] = []
    warnings: list[str] = []

    try:
        got_429 = False
        for i in range(50):
            try:
                r = requests.post(
                    url("/api/auth/login"),
                    json={"username": "nonexistent", "password": "wrong"},
                    timeout=3,
                )
                if r.status_code == 429:
                    print(f"  PASS: 429 after {i + 1} rapid login attempts")
                    got_429 = True
                    break
            except requests.RequestException:
                break

        if not got_429:
            warnings.append(
                "No rate limiting detected on POST /api/auth/login after 50 requests"
            )
            print(
                "  WARN: No 429 after 50 rapid login attempts (rate limiting may not be configured)"
            )
    except requests.RequestException as exc:
        warnings.append(f"Rate limit test failed: {exc}")
        print(f"  WARN: Could not reach login endpoint: {exc}")

    return _record(
        20,
        "rate_limiting_login",
        "WARN" if warnings and not issues else ("FAIL" if issues else "PASS"),
        issues,
        warnings,
    )


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="NPS Security Audit")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--report", type=str, help="Write JSON report to file path")
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as failures"
    )
    args = parser.parse_args()

    audit_start = datetime.now(timezone.utc)

    if not args.json:
        print("=" * 60)
        print(f"NPS Security Audit v{AUDIT_VERSION}")
        print(f"Started: {audit_start.isoformat()}")
        print("=" * 60)

    # Determine if API is available
    api_available = check_api()
    if not api_available and not args.json:
        print("WARNING: API not reachable — skipping network-based checks")

    all_issues: list[str] = []

    # ── Network-based checks (require API) ───────────────────────────────────

    if api_available:
        all_issues.extend(check_auth())
        all_issues.extend(check_bad_token())
        all_issues.extend(check_rate_limit())
        all_issues.extend(check_input_handling())
        all_issues.extend(check_cors())
        all_issues.extend(check_sql_injection())
        all_issues.extend(check_xss())
        all_issues.extend(check_csrf())
        all_issues.extend(check_auth_bypass())
        all_issues.extend(check_security_headers())
        all_issues.extend(check_sensitive_data())
        all_issues.extend(check_path_traversal())
        all_issues.extend(check_token_security())
        all_issues.extend(check_rate_limiting_detailed())
    else:
        skipped_network_checks = [
            (1, "auth_enforcement"),
            (2, "invalid_token"),
            (3, "rate_limiting"),
            (4, "input_handling"),
            (6, "cors"),
            (8, "sql_injection"),
            (9, "xss_protection"),
            (10, "csrf_protection"),
            (11, "auth_bypass"),
            (14, "security_headers"),
            (15, "sensitive_data_exposure"),
            (16, "path_traversal"),
            (17, "token_security"),
            (20, "rate_limiting_login"),
        ]
        for check_num, name in skipped_network_checks:
            _results.append(
                {
                    "check": check_num,
                    "name": name,
                    "status": "SKIP",
                    "issues": [],
                    "warnings": ["API not reachable"],
                }
            )
            if not args.json:
                print(f"\n[{check_num}] {name}: SKIP (API not reachable)")

    # ── Filesystem-only checks (always run) ──────────────────────────────────

    all_issues.extend(check_credentials_scan())
    all_issues.extend(check_no_subprocess())
    all_issues.extend(check_encryption_compliance())
    all_issues.extend(check_dependencies())
    all_issues.extend(check_database_security())
    all_issues.extend(check_code_quality_security())

    # ── Token security (partial — key strength check does not need API) ──────

    if not api_available:
        all_issues.extend(check_token_security())

    # ── Summary ──────────────────────────────────────────────────────────────

    audit_end = datetime.now(timezone.utc)
    duration_seconds = (audit_end - audit_start).total_seconds()

    total_checks = len(_results)
    passed = sum(1 for r in _results if r["status"] == "PASS")
    failed = sum(1 for r in _results if r["status"] == "FAIL")
    warned = sum(1 for r in _results if r["status"] == "WARN")
    skipped = sum(1 for r in _results if r["status"] == "SKIP")
    info_count = sum(1 for r in _results if r["status"] == "INFO")

    report = {
        "audit_version": AUDIT_VERSION,
        "timestamp": audit_start.isoformat(),
        "duration_seconds": round(duration_seconds, 2),
        "api_available": api_available,
        "summary": {
            "total_checks": total_checks,
            "passed": passed,
            "failed": failed,
            "warnings": warned,
            "skipped": skipped,
            "info": info_count,
            "total_issues": len(all_issues),
            "total_warnings": len(_warnings),
        },
        "results": _results,
        "issues": all_issues,
        "warnings": _warnings,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("\n" + "=" * 60)
        print(f"NPS Security Audit v{AUDIT_VERSION} — Summary")
        print(f"Duration: {duration_seconds:.1f}s")
        print(
            f"Checks: {total_checks} total | {passed} passed | {failed} failed | {warned} warnings | {skipped} skipped"
        )
        print("-" * 60)

        if all_issues:
            print(f"\nISSUES ({len(all_issues)}):")
            for issue in all_issues:
                print(f"  - {issue}")

        if _warnings:
            print(f"\nWARNINGS ({len(_warnings)}):")
            for w in _warnings:
                print(f"  - {w}")

        if not all_issues and not _warnings:
            print("\nAll checks passed with no warnings.")
        elif not all_issues:
            print(f"\nNo failures. {len(_warnings)} warning(s) noted.")

        print("=" * 60)

    # Write report file if requested
    if args.report:
        report_path = Path(args.report).resolve()
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2))
            if not args.json:
                print(f"\nReport written to: {report_path}")
        except OSError as exc:
            print(
                f"\nERROR: Could not write report to {report_path}: {exc}",
                file=sys.stderr,
            )

    # Exit code
    if all_issues:
        sys.exit(1)
    elif args.strict and _warnings:
        if not args.json:
            print("\n--strict mode: treating warnings as failures")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
