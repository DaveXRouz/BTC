# Specs

V4 session specification files for Claude Code execution.

## Purpose

Each file in this folder contains a prompt that sets context for a specific coding session. Load the relevant prompt at the start of each session to maintain continuity.

## Naming Convention

```
YYYY-MM-DD_session_name.md
```

**Examples:**

- `2026-02-08_phase1_database_setup.md`
- `2026-02-09_api_auth_middleware.md`
- `2026-02-10_rust_scanner_crypto.md`

## Usage

1. Before starting a session, create a new file following the naming convention
2. Include context from the previous session's outcomes
3. Specify the objectives for the current session
4. Reference any relevant files from `memory/` or `project_knowledge_base/`

## Template

```markdown
# Session: YYYY-MM-DD - [Session Name]

## Context

[What was accomplished in the previous session]
[Current state of the project]

## Objectives

1. [Primary goal]
2. [Secondary goal]
3. [Stretch goal]

## Key Files

- `path/to/relevant/file1`
- `path/to/relevant/file2`

## Constraints

[Any limitations, deadlines, or requirements]

## Notes

[Additional context for the AI]
```
