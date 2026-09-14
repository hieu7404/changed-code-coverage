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

## D012 — Local sample SDK and test framework
**Accepted**

WP0 confirmed SDK 10.0.401 can build the `net10.0` sample and run 7 passing tests.
The sample pins SDK 10.0.401 with `latestPatch` roll-forward in its own `global.json`.
Run the SDK from inside `sample-dotnet/` to apply that selection.

The initial machine had Git 2.55.0 and Python 3.14.6, but no .NET SDK.
Use an optional repository-local SDK under `artifacts/tools/dotnet/`, with CLI state
and NuGet packages under `artifacts/tools/`; no global PATH or Git configuration was changed.
A fresh checkout needs an SDK and initial package restore.
Instructions are in [the sample README](../sample-dotnet/README.md).

The new sample uses xUnit 2.9.3, xunit.runner.visualstudio 3.1.4, and
Microsoft.NET.Test.Sdk 17.14.1, as provided by the installed SDK's xUnit template.
Coverage setup remains WP1; the template's collector reference was removed for WP0.

## D013 — Controlled discount policy with an intentional test gap
**Accepted**

Use one `DiscountService` with negative-input rejection, no discount below 100,
10% discount from 100 to below 1000, and 20% discount from 1000 upward.
Use decimal arithmetic without rounding. These are synthetic sample rules.

Seven deterministic test cases check rejection, zero, thresholds, and fixed totals.
The 20% return path is deliberately untested. WP1 must verify coverage evidence;
WP0 makes no measured line/branch coverage claim. No semantic branch identity is inferred.
The Python folders contain placeholders only until WP2.

## Pending decisions

Fill during implementation:

```text
Coverlet setup:
ReportGenerator setup:
Final CLI shape:
HTML renderer choice:
Real pilot repository when available:
Real pilot collector:
CI provider:
Threshold policy:
```
