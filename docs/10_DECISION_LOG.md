# Decision Log

## D001 — Standalone portable repository
**Accepted**

No absolute machine-specific paths or dependency on the old DMS workspace.

## D002 — Local controlled sample first
**Accepted**

Build/validate TC1 against a small C# sample before real company access is available.

## D003 — One real C# pilot later
**Accepted**

When access becomes available, validate TC1 on one existing C# project rather than widening to all languages.

## D004 — Existing test runner
**Accepted**

Reuse the pilot's test framework.

## D005 — Cobertura XML
**Accepted**

Use Cobertura XML as the initial normalized coverage format.

## D006 — Deterministic Python mapper
**Accepted**

Python handles:
- Git diff;
- XML parsing;
- path normalization;
- changed line/branch mapping;
- metrics;
- TC1-specific reports.

## D007 — Three-state result
**Accepted**

```text
covered
uncovered
unknown
```

## D008 — Branch coverage only where reliable
**Accepted**

Do not invent branch semantics.

## D009 — ReportGenerator as supporting visualization
**Accepted**

It does not replace TC1 mapping.

## D010 — CI starts non-blocking
**Accepted**

Gate only after mapping validation and explicit threshold decision.

## D011 — Generated output under artifacts
**Accepted**

All generated reports, coverage exports, test-run results/logs, and evaluation results
belong under the repository-root `artifacts/`, regardless of size, and are not committed.
Build intermediates and tool caches keep their standard gitignored locations.
Small reviewed fixtures and expected results remain committed under `fixtures/` and `eval/`.
Durable documentation remains under `docs/`.

The [architecture output policy](03_ARCHITECTURE.md#generated-output-policy) defines
the subdirectories. Ignore the artifact root rather than coverage filenames throughout
the repository so coverage fixtures remain trackable.

## Pending decisions

Fill during implementation:

```text
Local sample target framework:
Local sample test framework:
Coverlet setup:
ReportGenerator setup:
Final CLI shape:
HTML renderer choice:
Real pilot repository when available:
Real pilot collector:
CI provider:
Threshold policy:
```
