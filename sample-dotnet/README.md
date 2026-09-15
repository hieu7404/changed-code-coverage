# Local C# Pilot

WP0 and WP1 are complete: all 7 tests pass and the coverage baseline is validated.

## Contents

- `Tc1.Sample/DiscountService.cs`: a pure decimal calculation with deterministic branches.
- `Tc1.Sample.Tests/DiscountServiceTests.cs`: fixed expected results and invalid-input checks.
- `Tc1.Sample.slnx`: the library and test project.
- `global.json`: SDK 10.0.401, allowing later patches in the same feature band.
- `NuGet.Config`: public nuget.org package source; no company feed required.

The target is `net10.0`. Tests use xUnit 2.9.3, the Visual Studio adapter 3.1.4,
and Microsoft.NET.Test.Sdk 17.14.1. The TC1 engine must not depend on this sample's rules.

## Sample contract

This is a synthetic policy, not a production business rule. No rounding is applied.

| Subtotal | Result | WP0 test inputs |
| --- | --- | --- |
| Below 0 | Throw ArgumentOutOfRangeException for subtotal | -1, -100 |
| 0 to below 100 | No discount | 0, 99 |
| 100 to below 1000 | 10% discount | 100, 250, 999 |
| 1000 and above | 20% discount | Intentionally not tested |

The last path is deliberately omitted to provide a known test gap for WP1.
WP1 has verified this test gap against real Cobertura and ReportGenerator output.
See the coverage baseline link below for measured line hits and branch aggregates.

## Run with an installed SDK

From the repository root, using PowerShell:

```powershell
Push-Location sample-dotnet
dotnet --version
dotnet restore Tc1.Sample.slnx --configfile NuGet.Config
dotnet build Tc1.Sample.slnx --no-restore --configuration Debug
dotnet test Tc1.Sample.slnx --no-build --configuration Debug --results-directory ../artifacts/test-results/wp0 --logger "trx;LogFileName=sample-tests.trx"
Pop-Location
```

Run inside `sample-dotnet/` so the CLI discovers its `global.json`.
Stop and resolve any failed command before continuing.

## Optional repository-local SDK on Windows

The initial machine had Git 2.55.0 and Python 3.14.6, but only .NET 6 runtime,
with no SDK. WP0 installed SDK 10.0.401 under `artifacts/tools/dotnet/`.
It did not change global PATH or install a machine-wide SDK.
The SDK/cache is ignored by Git and must be installed again on a fresh checkout.

To reproduce that installation from the repository root (requires internet):

```powershell
New-Item -ItemType Directory -Force artifacts/tools | Out-Null
Invoke-WebRequest -UseBasicParsing https://dot.net/v1/dotnet-install.ps1 -OutFile artifacts/tools/dotnet-install.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File artifacts/tools/dotnet-install.ps1 -Version 10.0.401 -InstallDir artifacts/tools/dotnet -NoPath
```

See Microsoft's [dotnet-install documentation](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-install-script).

Then run these commands from the repository root. Environment variables apply only
to this PowerShell session; SDK state and NuGet packages stay under `artifacts/`.

```powershell
$wp0Root = (Get-Location).Path
$env:DOTNET_ROOT = Join-Path $wp0Root 'artifacts/tools/dotnet'
$env:DOTNET_CLI_HOME = Join-Path $wp0Root 'artifacts/tools/dotnet-home'
$env:NUGET_PACKAGES = Join-Path $wp0Root 'artifacts/tools/nuget-packages'
$env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
$env:DOTNET_GENERATE_ASPNET_CERTIFICATE = 'false'
$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE = '1'
$wp0Dotnet = Join-Path $env:DOTNET_ROOT 'dotnet.exe'

Push-Location sample-dotnet
& $wp0Dotnet --version
& $wp0Dotnet restore Tc1.Sample.slnx --configfile NuGet.Config
& $wp0Dotnet build Tc1.Sample.slnx --no-restore --configuration Debug
& $wp0Dotnet test Tc1.Sample.slnx --no-build --configuration Debug --results-directory ../artifacts/test-results/wp0 --logger "trx;LogFileName=sample-tests.trx"
Pop-Location
```

Stop and resolve any failed command before continuing. Commands assume the repository
root is the starting directory and use no machine-specific paths.

## Validated results and next step

- Debug build: 0 warnings, 0 errors.
- Tests: 7 passed, 0 failed, 0 skipped.
- WP0 evidence: artifacts/test-results/wp0/sample-tests.trx.
- WP1 baseline: 10/12 instrumented lines and 5/6 branch outcomes covered (83.33% each).
- The 20% return at L16 has zero hits; L13 has positive hits but branch coverage is 1/2.
- Python bootstrap is complete; see [WP2 setup](../docs/14_PYTHON_BOOTSTRAP.md).

## Collect coverage

From the repository root using the local SDK:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File sample-dotnet/Collect-Coverage.ps1 -Dotnet ./artifacts/tools/dotnet/dotnet.exe
```

The script restores pinned Coverlet 6.0.4 and ReportGenerator 5.5.11, builds, tests,
selects the current TRX coverage attachment, and generates the baseline bundle.

Open artifacts/tc1/coverage/index.html.
Cobertura is at artifacts/tc1/coverage.cobertura.xml; raw run evidence and logs are under
artifacts/test-results/wp1-<uuid>/. All generated output is ignored by Git.

See [the WP1 runbook](../docs/13_COVERAGE_BASELINE.md) for exact evidence,
denominators, reproducibility, branch limitations and the resolved local policy blocker.
These are whole-sample metrics; changed-code mapping is not implemented yet.
