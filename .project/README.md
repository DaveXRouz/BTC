# Project

Project architecture plans and Claude workflow guides.

## Purpose

This folder organizes reference materials that inform the NPS V4 build process. Unlike `memory/` (which tracks session activity), this folder stores durable reference documents.

## Suggested Organization

```
project_knowledge_base/
├── specs/          ← Feature specifications and requirements
├── architecture/   ← System design documents and diagrams
├── research/       ← Technology evaluations, benchmarks, comparisons
└── decisions/      ← Architecture Decision Records (ADRs)
```

Create subfolders as needed when the collection grows.

## What to Store Here

- Feature specifications and requirements documents
- Architecture diagrams and design documents
- Technology research and comparison notes
- API documentation and contracts
- Performance benchmarks and analysis
- Security audit notes
- Third-party integration guides
- Architecture Decision Records (ADRs)

## Usage

1. Add documents using a descriptive filename
2. Use markdown format for consistency
3. Include dates in filenames for time-sensitive documents
4. Cross-reference from `memory/` session notes when relevant

## File Naming

```
descriptive_name.md
YYYY-MM-DD_topic.md  (for time-sensitive docs)
```

**Examples:**

- `v4_api_contract.md`
- `rust_scanner_benchmarks.md`
- `2026-02-08_encryption_comparison.md`
