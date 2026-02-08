# Long-Term Memory

**Retention:** Permanent

## Purpose

Preserves important project history including completed phases, major architectural decisions, key learnings, and milestone achievements. These records form the permanent knowledge base of the project's evolution.

## Retention Policy

- Files are **never deleted** — they form the project's permanent record
- Each file represents a significant milestone or achievement
- Update `../INDEX.md` when adding new milestones

## What Belongs Here

- Completed build phases
- Major architecture decisions and their reasoning
- Significant performance improvements with metrics
- Breaking changes and migration notes
- Key learnings that apply to future work

## Usage

1. Copy `TEMPLATE_MILESTONE.md` to a new file: `YYYY-MM-DD_milestone_name.md`
2. Fill in all sections with measurable details
3. Include verification proof (commands + expected output)
4. Update `../INDEX.md` with the new milestone entry

## File Naming

```
YYYY-MM-DD_milestone_name.md
```

**Examples:**

- `2026-02-10_phase1_database_complete.md`
- `2026-02-15_rust_scanner_mvp.md`
