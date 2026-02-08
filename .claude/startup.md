# Claude Code Startup Protocol

> This file defines EXACTLY what happens when Claude Code opens a session.
> Referenced by CLAUDE.md step 3.

---

## Silent Boot Checks (No Output to User)

Run these checks automatically and silently at session start. Only report problems.

### Check 1: Project Structure Verification
```bash
# Verify critical files exist
test -f CLAUDE.md && test -f SESSION_LOG.md && test -f docker-compose.yml
test -d api/ && test -d frontend/ && test -d services/ && test -d database/
```
**If missing:** Report to user which files/folders are missing.

### Check 2: Git Status
```bash
git status --short
git log --oneline -1
```
**Store internally:** last commit hash and message. Use for SESSION_LOG context.

### Check 3: Environment File
```bash
test -f .env
```
**If missing:** Warn user: "No .env file found. Copy from .env.example before running services."

### Check 4: Dependency State (silent, fast)
```bash
# Python (check if venv or packages exist)
test -f api/pyproject.toml
test -d services/oracle/oracle_service/

# Node (check if node_modules exists)
test -d frontend/node_modules/

# Rust (check if Cargo.toml exists)
test -f services/scanner/Cargo.toml
```
**If node_modules missing:** Auto-run `cd frontend && npm install` silently.
**If Python packages missing:** Auto-run `cd api && pip install -e ".[dev]"` silently.

### Check 5: Docker Status (optional, fast)
```bash
docker-compose ps 2>/dev/null | grep -c "Up"
```
**Don't start Docker automatically.** Just note internally if services are running.

---

## Post-Boot: Session Detection

After silent checks, determine session mode:

### Mode A: User says "continue" / "next" / "go" / says nothing
```
1. Read SESSION_LOG.md
2. Find last completed session entry
3. Find "Next:" field from last entry
4. Show 1-line: "Continuing session [N]: [task from Next field]"
5. If a spec file is referenced → read it → create comprehensive plan → show plan → wait for approval
6. If task is clear without spec → proceed directly
```

### Mode B: User gives specific task
```
1. Understand the task
2. Check if it aligns with current session block (SESSION_LOG.md)
3. If task needs a spec → read relevant .specs/ file
4. Create plan if complex, execute directly if simple
5. Do the work silently
6. Show results
```

### Mode C: User uploads a ZIP file
```
1. Extract and catalog contents
2. Compare with existing project structure
3. Identify what changed or was added
4. Report findings to user
5. Ask: "What should I do with these changes?"
```

---

## Dependency Auto-Install Rules

### Known Safe (install silently):
- Everything in `api/pyproject.toml` [dependencies]
- Everything in `frontend/package.json` [dependencies + devDependencies]
- Everything in `services/oracle/pyproject.toml` [dependencies]
- Everything in `services/scanner/Cargo.toml` [dependencies]
- Standard development tools: pytest, ruff, black, mypy, eslint, prettier

### Ask First:
- Any package not already in a project manifest file
- System-level packages (apt-get, brew)
- Database tools (pgcli, dbeaver, etc.)
- New MCP servers or plugins

### After Any Install:
```bash
# Python
pip-audit 2>/dev/null || echo "pip-audit not installed"

# Node
cd frontend && npm audit --audit-level=moderate 2>/dev/null

# Report vulnerabilities to user if found
```

---

## Auto-Format Configuration

### On Every File Save:

**Python:**
```bash
black <file> --line-length 100
ruff check <file> --fix
```

**TypeScript/React:**
```bash
cd frontend && npx prettier --write <file>
cd frontend && npx eslint --fix <file>
```

**Rust:**
```bash
cd services/scanner && cargo fmt
cargo clippy -- -D warnings
```

### On Every Session End:
```bash
# Full project format check
cd api && black . --check --line-length 100
cd frontend && npx prettier --check "src/**/*.{ts,tsx}"
cd services/scanner && cargo fmt --check
```

---

## Security Scan (Every Commit)

Before every `git commit`, run:

```bash
# Check for leaked secrets
grep -rn "sk-ant-\|AKIA\|password\s*=\s*['\"]" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.rs" . \
  --exclude-dir=.archive --exclude-dir=node_modules --exclude-dir=target --exclude=.env.example

# Check for hardcoded IPs/URLs that should be env vars
grep -rn "localhost:[0-9]\+" --include="*.py" --include="*.ts" . \
  --exclude-dir=node_modules --exclude-dir=.archive --exclude="*.test.*" --exclude="*.spec.*" --exclude="vite.config.*"
```

**If secrets found:** STOP. Do NOT commit. Remove the secret. Use .env variable instead.

---

## Git Stash Safety Net

Before ANY of these operations, auto-run `git stash`:
- Deleting files
- Rewriting more than 3 files at once
- Changing database schemas
- Modifying encryption/security code
- Changing Docker configuration

After operation completes successfully:
- Drop the stash: `git stash drop`

If operation fails:
- Restore: `git stash pop`
- Report the failure to user
