# Documentation map

TC1's local end-to-end coverage review flow is implemented. Start with the
[README](../README.md), then choose the document for your task.

| Need | Read |
| --- | --- |
| Install, collect coverage, analyze a diff, open reports | [End-to-end runbook](01_DEMO_RUNBOOK.md) |
| Understand mapping, denominators, CLI and report contracts | [Architecture and coverage rules](02_ARCHITECTURE.md) |
| See what works and what remains | [Current status](03_TASK_CHECKLIST.md) |
| Reproduce evaluation or validate a real C# pilot | [Validation](04_EVALUATION_PLAN.md) |
| Understand accepted design choices | [Decision log](05_DECISION_LOG.md) |
| Consider later work and CI prerequisites | [Future work](06_FUTURE_WORK.md) |

Local references: [C# sample](../sample-dotnet/README.md),
[evaluation assets](../eval/README.md), [fixtures](../fixtures/README.md),
and [contributor rules](../AGENTS.md).

These seven documents describe current behavior. Earlier work-package plans,
bootstrap prompts and implementation diaries are retained in Git history rather
than duplicated in the active documentation. Files are numbered consecutively
from `00` to `06` in the reading order above.

**Product boundary:** TC1 supplies report-only evidence for review. CI automation
has not been implemented, and no trusted coverage threshold has been established
for a blocking gate.
