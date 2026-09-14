# Codex Workflow

## First action on every substantial task

Read:

```text
AGENTS.md
README.md
docs/00_START_HERE.md
```

Then open only the docs relevant to the task.

## Do not assume external context

This standalone project must not depend on:
- the old DMS absolute path;
- another user's workstation;
- a private workspace;
- a company-specific artifact folder.

If later given external repo access, integrate it explicitly as a pilot.

## Implementation style

Prefer:
- small modules;
- explicit models;
- tests first/alongside logic;
- deterministic results;
- clear errors.

Avoid:
- giant scripts;
- silent fallbacks;
- guessed path matches;
- scope expansion.

## Scope gate

Before implementing anything not in MVP, check whether it belongs in:

```text
docs/11_FUTURE_WORK.md
```

Examples:
- LLM explanation;
- Graft;
- OpenCodeReview;
- blast radius;
- dashboard.

Do not implement them without user approval.

## Handoff

After a work package:

```text
Scope
Changed files
Commands run
Tests/validation
Result
Limitations
Next step
```
