# Memory

AI session memory tracking system with short-term and long-term separation.

## Structure

```
memory/
├── README.md          ← You are here
├── INDEX.md           ← Master list of all sessions and milestones
├── short_term/        ← Recent session notes (7-day retention)
│   ├── README.md      ← Retention policy
│   └── TEMPLATE_SESSION.md
└── long_term/         ← Permanent records
    ├── README.md      ← Retention policy
    └── TEMPLATE_MILESTONE.md
```

## Short-Term Memory (7-day retention)

Captures day-to-day session activity:

- Daily session notes
- Quick decisions
- Temporary findings
- Iteration notes

Files older than 7 days should be archived or deleted during cleanup. Key decisions should be promoted to long-term memory before archival.

## Long-Term Memory (permanent)

Preserves important project history:

- Completed phases
- Major decisions and their reasoning
- Architecture changes
- Key learnings
- Milestone achievements

## Workflow

1. **Start of session:** Check `INDEX.md` for context on recent sessions
2. **During session:** Note decisions and changes as you go
3. **End of session:** Create a session file from `TEMPLATE_SESSION.md` in `short_term/`
4. **At milestones:** Create a milestone file from `TEMPLATE_MILESTONE.md` in `long_term/`
5. **Weekly cleanup:** Archive short-term files older than 7 days, promote key items to long-term

## Index

See [INDEX.md](INDEX.md) for the master list of all sessions and milestones.
