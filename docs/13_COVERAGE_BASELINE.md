# WP1 Coverage Baseline

## Status

**WP1 complete.** SDK 10.0.401, Coverlet collector 6.0.4 and ReportGenerator 5.5.11
completed the local pipeline on 2026-09-14. Debug build had 0 warnings and 0 errors;
all 7 xUnit tests passed. Cobertura and ReportGenerator HTML were generated and checked.

Validated run: `wp1-cf63f6c6500d4b6f878108c168eeb6ca`.
The sample source is unchanged from WP0 commit `4400849`.
The run's metadata records source and coverage SHA-256 hashes.

## Configuration

- Retain the WP0 xUnit/VSTest runner and `net10.0` target.
- Pin `coverlet.collector` 6.0.4 in the test project.
- Pin ReportGenerator 5.5.11 in `sample-dotnet/.config/dotnet-tools.json`.
- `coverage.runsettings` exports Cobertura and includes only `[Tc1.Sample]*`.
- Test assemblies are explicitly excluded; no source-file or attribute exclusions are added.
- Preserve hit counts (`SingleHit=false`) and source paths (`UseSourceLink=false`).
- Disable ReportGenerator's risk-hotspot selection; generate HTML and text summary.

The collector/tool combination is validated for this controlled sample.
Configuration references:
[Coverlet 6.0.4 VSTest guide](https://github.com/coverlet-coverage/coverlet/blob/v6.0.4/Documentation/VSTestIntegration.md)
and [ReportGenerator usage](https://github.com/danielpalme/ReportGenerator).

## Reproduce

From the repository root on Windows, with the WP0 local SDK installed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File sample-dotnet/Collect-Coverage.ps1 -Dotnet ./artifacts/tools/dotnet/dotnet.exe
```

The PowerShell execution-policy option applies to that script process only;
it does not change Windows Application Control.

With a compatible SDK on PATH:

```powershell
powershell -NoProfile -File sample-dotnet/Collect-Coverage.ps1
```

PowerShell 7 users can invoke the script with `pwsh` and an explicit `-Dotnet`
executable. Other operating systems have not been validated.

The script restores dependencies/tools, builds, runs tests with coverage, verifies all
discovered tests passed and at least one executed, then reads the Coverlet attachment
declared in that run's TRX. It rejects missing/multiple attachments, paths outside the
current run, and empty line evidence. ReportGenerator must succeed and produce HTML
before the script publishes the bundle.

VSTest writes both a collector export and a duplicate under the TRX deployment
directory. The two files were observed to have identical hashes. Resolve
`TestSettings/Deployment/@runDeploymentRoot` plus `In/` and the Coverlet attachment's
`href`; do not recursively count exports or pick the first file found.

Paths resolve from the script directory. CLI state and packages stay under
`artifacts/tools/`; process environment variables and working directory are restored.
Each run uses its own UUID directory. Do not run collections concurrently against
the same build/bundle directories.

## Output contract

| Path | Contents |
| --- | --- |
| `artifacts/test-results/wp1-<uuid>/` | TRX, raw collector attachments and collection transcript |
| `artifacts/test-results/wp1-<uuid>/coverage/` | ReportGenerator HTML and text summary |
| `artifacts/test-results/wp1-<uuid>/run.json` | Successful run ID, SDK/tool versions and hashes |
| `artifacts/tc1/coverage.cobertura.xml` | Byte-for-byte copy of the selected Cobertura export |
| `artifacts/tc1/coverage/` | Published ReportGenerator HTML and summary |
| `artifacts/tc1/coverage-run.json` | Metadata identifying the published successful run |

Cobertura is already the normalized format; no format conversion or rewriting of
evidence is needed. Raw and bundled XML hashes match. Generated XML retains the
collector's source root and filename; combining them resolves the actual sample source.
General repository path normalization remains WP5. All generated output is ignored by Git.

The published directory is for this single controlled sample. A failed command does
not establish a new baseline; use `coverage-run.json` to identify any existing bundle.

## Verified evidence

Use class-level `class/lines/line` entries once. The same evidence is also present under
methods and must not be counted twice.

| Metric | Observed |
| --- | --- |
| Assemblies / classes / source files | 1 / 1 / 1 |
| Tests passed / failed / skipped | 7 / 0 / 0 |
| Covered / uncovered instrumented lines | 10 / 2 |
| Line denominator | 12 |
| Line coverage | 10/12 = 83.33%; ReportGenerator displays 83.3% |
| Covered / total branch outcomes | 5 / 6 |
| Branch coverage | 5/6 = 83.33%; ReportGenerator displays 83.3% |

These are **whole-sample coverage metrics**, not changed-code metrics.
The collector's rounded XML rate is retained unchanged; counts explain the denominator.

| DiscountService.cs location | XML hits | HTML/evidence interpretation |
| --- | --- | --- |
| L10: reject negative subtotal | 2 | Covered |
| L14: opening brace of the bulk-discount block | 0 | Instrumented sequence point, uncovered |
| L16: return the 20% discount | 0 | Uncovered, displayed red |
| L21: return the 10% discount | 3 | Covered |
| L24: return unchanged subtotal | 2 | Covered |
| L8: negative-subtotal condition | 7 | Aggregate 100% (2/2) |
| L13: bulk-discount condition | 5 | Aggregate 50% (1/2), displayed orange |
| L19: standard-discount condition | 5 | Aggregate 100% (2/2) |

L13 has positive line hits, so its line is covered. ReportGenerator labels the row
"Partially covered" because branch coverage at that location is incomplete.
Cobertura provides jump identifiers (14, 46, 84) and aggregate condition percentages;
these do not establish semantic true/false branch identities.

Debug instrumentation includes braces/sequence points. The 2 uncovered lines are
L14 and L16, not two separate business statements. Do not discard explicit entries
merely because a line contains a brace.

All 12 class-level line entries and three branch aggregates were checked against the
HTML rows. The HTML index/class page's local links resolve, and source and XML hashes
match metadata. Recorded checks:
`artifacts/test-results/wp1-cf63f6c6500d4b6f878108c168eeb6ca/manual-validation.json`.
That file records this review; it is not automatically produced by the collection script.

## Limitations and prior blocker

There is no Git diff mapping yet, so no changed-code unknown/excluded counts exist.
Missing coverage entries must remain unknown in the future mapper unless an explicit
exclusion is established. Unknown/excluded evidence is outside classifiable denominators;
a zero denominator must produce null, not 0%. HTML's "Not coverable" presentation alone
does not establish a TC1 exclusion.

Initial runs were blocked by Windows Smart App Control policy
`VerifiedAndReputableDesktop` with `0x800711C7`. The user identified the policy in
Event Viewer and reported disabling it on their personal machine. Subsequent tests
and ReportGenerator ran successfully; no policy changes were made by the script.
Original failed evidence remains under
`artifacts/test-results/wp1-508355f1fada4afba463efe8e03db2d5/` and
`artifacts/test-results/wp1-diagnostic/`; it is not a valid coverage baseline.

The first successful test run then exposed duplicate XML attachment handling.
The script was corrected to use TRX attachment metadata and the complete pipeline
was rerun successfully. This validation covers one local sample and configuration;
real-pilot collection, other platforms, changed-code mapping and CI remain later work.

Next bounded step: WP2 Python package bootstrap, CLI skeleton, shared models,
error types and pytest setup.