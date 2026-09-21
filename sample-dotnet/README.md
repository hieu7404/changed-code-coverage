# Controlled C# sample

This sample supplies real coverage evidence for TC1's local end-to-end flow.
Start with the [runbook](../docs/01_DEMO_RUNBOOK.md) to collect coverage and analyze
committed changes.

## Current sample contract

`Tc1.Sample/DiscountService.cs` implements a synthetic decimal policy without rounding:

| Subtotal | Current result | Existing tests |
| --- | --- | --- |
| Below 0 | Throw `ArgumentOutOfRangeException` | -1, -100 |
| 0 to below 100 | No discount | 0, 99 |
| 100 to below 1000 | Multiply by `0.90m` (10% discount) | 100, 250, 999 |
| 1000 and above | Multiply by `0.75m` (25% discount) | Intentionally untested |

Seven xUnit cases leave the bulk return uncovered intentionally. The original
baseline used `0.80m` for that path; see [recorded validation](../docs/04_EVALUATION_PLAN.md#recorded-c-baseline).
The TC1 engine does not depend on these business rules.

## Tooling

The sample targets `net10.0`. [global.json](global.json) pins SDK 10.0.401 with
`latestPatch` roll-forward. Run direct `dotnet` commands inside this directory so
that SDK selection applies. The projects use xUnit 2.9.3, adapter 3.1.4,
Microsoft.NET.Test.Sdk 17.14.1 and Coverlet collector 6.0.4.
The local tool manifest pins ReportGenerator 5.5.11; `NuGet.Config` uses nuget.org.

For build/tests only, from the repository root:

```bash
cd sample-dotnet
dotnet restore Tc1.Sample.slnx --configfile NuGet.Config
dotnet build Tc1.Sample.slnx --no-restore --configuration Debug
dotnet test Tc1.Sample.slnx --no-build --configuration Debug --results-directory ../artifacts/test-results/sample --logger "trx;LogFileName=sample-tests.trx"
cd ..
```

Stop on a failed command. To run the full test/coverage/ReportGenerator collection
from the repository root instead:

```powershell
powershell -NoProfile -File sample-dotnet/Collect-Coverage.ps1
```

Use `pwsh` for PowerShell 7, or pass `-Dotnet` to select an installed executable.
The script resolves paths itself and restores its process environment afterward.
It includes only `Tc1.Sample`, excludes test assemblies, preserves line hit counts
and disables ReportGenerator risk-hotspot selection.

Selected XML, supporting HTML and run metadata go under `artifacts/tc1/`; raw runs
and logs go under `artifacts/test-results/`. Collection does not run the TC1 analyzer:
continue with [report generation](../docs/01_DEMO_RUNBOOK.md#4-generate-tc1-reports).
