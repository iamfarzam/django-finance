# Decision Log (ADRs)

Architecture Decision Records capture important decisions, their context, and consequences.

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-adr-template.md) | ADR Template | - | - |
| [0002](0002-tech-stack-selection.md) | Tech Stack Selection | Accepted | 2026-02-07 |
| [0003](0003-b2c-saas-requirements.md) | B2C SaaS Requirements | Accepted | 2026-02-07 |

## Purpose

ADRs document significant decisions that affect:
- System architecture and structure
- Technology or infrastructure choices
- Security and compliance posture
- Cross-cutting concerns

## When to Write an ADR

Create an ADR when:
- Choosing between multiple valid approaches
- Making technology or framework decisions
- Changing architectural patterns
- Establishing security policies
- Defining standards that affect multiple modules

## Format

Use the template in `0001-adr-template.md`:

```markdown
# ADR-NNNN: Title

## Status
Proposed | Accepted | Superseded | Deprecated

## Date
YYYY-MM-DD

## Context
What is the issue? What forces are at play?

## Decision
What is the change being proposed?

## Consequences
What becomes easier or harder?
```

## Naming Convention

- Format: `NNNN-kebab-case-title.md`
- Number: Incremental, zero-padded to 4 digits
- Title: Short, descriptive, lowercase with hyphens

## Workflow

1. Create new ADR with status "Proposed"
2. Discuss in team review
3. Update status to "Accepted" or "Rejected"
4. If superseded, update status and link to new ADR
