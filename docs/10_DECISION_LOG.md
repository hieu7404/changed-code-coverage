# Decision Log

## D001 â€” Standalone portable repository
**Accepted**

No absolute machine-specific paths or dependency on the old DMS workspace.

## D002 â€” Local controlled sample first
**Accepted**

Build/validate TC1 against a small C# sample before real company access is available.

## D003 â€” One real C# pilot later
**Accepted**

When access becomes available, validate TC1 on one existing C# project rather than widening to all languages.

## D004 â€” Existing test runner
**Accepted**

Reuse the pilot's test framework.

## D005 â€” Cobertura XML
**Accepted**

Use Cobertura XML as the initial normalized coverage format.

## D006 â€” Deterministic Python mapper
**Accepted**

Python handles:
- Git diff;
- XML parsing;
- path normalization;
- changed line/branch mapping;
- metrics;
- TC1-specific reports.

## D007 â€” Three-state result
**Accepted**

```text
covered
uncovered
unknown
```

## D008 â€” Branch coverage only where reliable
**Accepted**

Do not invent branch semantics.

## D009 â€” ReportGenerator as supporting visualization
**Accepted**

It does not replace TC1 mapping.

## D010 â€” CI starts non-blocking
**Accepted**

Gate only after mapping validation and explicit threshold decision.

## D011 â€” Generated output under artifacts
**Accepted**

All generated reports, coverage exports, test-run results/logs, and evaluation results
belong under the repository-root `artifacts/`, regardless of size, and are not committed.
Build intermediates and tool caches keep their standard gitignored locations.
Small reviewed fixtures and expected results remain committed under `fixtures/` and `eval/`.
Durable documentation remains under `docs/`.

The [architecture output policy](03_ARCHITECTURE.md#generated-output-policy) defines
the subdirectories. Ignore the artifact root rather than coverage filenames throughout
the repository so coverage fixtures remain trackable.

## D012 â€” Local sample SDK and test framework
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

## D013 â€” Controlled discount policy with an intentional test gap
**Accepted**

Use one `DiscountService` with negative-input rejection, no discount below 100,
10% discount from 100 to below 1000, and 20% discount from 1000 upward.
Use decimal arithmetic without rounding. These are synthetic sample rules.

Seven deterministic test cases check rejection, zero, thresholds, and fixed totals.
The 20% return path is deliberately untested. WP1 must verify coverage evidence;
WP0 makes no measured line/branch coverage claim. No semantic branch identity is inferred.
The Python folders contain placeholders only until WP2.

## D014 â€” Validated sample coverage collector and visualization
**Accepted**

WP1 validates Coverlet collector 6.0.4 with the existing xUnit/VSTest runner on
net10.0 / SDK 10.0.401, plus local ReportGenerator 5.5.11.
The sample runsettings include only Tc1.Sample and explicitly exclude test assemblies.
Keep Cobertura evidence unchanged; generate coverage HTML and text summary, with
risk-hotspot selection disabled. All tool caches and generated evidence stay under artifacts.

Select the Coverlet attachment declared by the current successful run's TRX deployment
metadata. VSTest creates duplicate physical exports; recursive file counting is not a
reliable way to determine how many collector attachments exist. Reject missing or
ambiguous attachments instead of choosing the first file.

The validated run passes all 7 tests, reports 10/12 instrumented lines and 5/6 branch
outcomes covered, and preserves raw/bundled XML hashes. Branch evidence is aggregate;
positive hits at a partially covered condition still mean the line is covered.
See [WP1 baseline evidence and limitations](13_COVERAGE_BASELINE.md).

## D015 â€” Python bootstrap and explicit CLI boundary
**Accepted**

WP2 uses a setuptools `src/` package, Python 3.11+, standard-library runtime code,
argparse, and pytest as a development extra. Both `tc1` and `python -m tc1` use the
same entry point and installed package version. Installation is local to `.venv/`.
Validated on Windows / Python 3.14.6 with pytest 9.1.1 and 43 passing tests.

The CLI accepts the runbook's analysis arguments but raises an explicit expected
error (exit 1) until the pipeline exists; help/version exit 0 and usage errors exit 2.
No report, metric, or implicit threshold is produced by the bootstrap.

Frozen records preserve opaque paths, explicit hits, raw condition metadata and
aggregate branch counts. Unknown and explicit exclusions remain distinct. All future
renderers will consume one `AnalysisResult`; metrics stay in WP8. These internal
models can evolve with parser/mapping work before the public report schema is finalized.
See [WP2 contracts and reproduction](14_PYTHON_BOOTSTRAP.md).

## D016 â€” Explicit merge-base comparison and Git diff limitations
**Accepted**

WP3 resolves base/head to commits, requires exactly one merge base, and compares
merge-base to head (`base...head` semantics). Missing or ambiguous history fails
explicitly. Staged/unstaged/untracked content does not enter the committed diff.

Use NUL-delimited raw inventory and literal per-file patches so paths are not guessed
from quoted headers. Disable external diff/textconv, rename detection and context;
validate hunk bodies before accepting head-line candidates. Preserve file kinds,
modes, binary flags and unavailable reasons. Deleted/binary/non-regular files remain
visible without fabricated source candidates or automatic coverage exclusions.

Renames are deleted plus added; copies are added. No rename/copy identity is inferred.
Coverage classification and denominator logic remain in later work packages.
The CLI now reads Git changes then exits explicitly before the unavailable WP4-WP9 stages.
See [WP3 validation and limitations](15_GIT_DIFF_PARSER.md).

## D017 â€” Preserve Cobertura records before mapping
**Accepted**

WP4 uses standard-library XML parsing for the validated Coverlet/Cobertura profile.
Require explicit filename, positive line number and nonnegative integer hits.
Missing line entries remain missing; malformed explicit records fail without defaulting
hits to zero. Preserve source strings, repeated records and raw branch metadata.

Class-level lines form the primary inventory; method-level lines are retained separately
without fallback or double counting. Duplicates are not merged or overwritten; the mapper
must establish reliability before classifying them. Root summary rates do not create
coverage evidence. Branch interpretation remains WP7.

Accept namespace-free and consistently namespaced XML. Reject unsupported structure
and DOCTYPE declarations explicitly; the validated Coverlet export has no DTD.
The CLI resolves Git inputs, reads the coverage path relative to the caller's working
directory, and then stops before WP5-WP9. Input bytes and report destinations are preserved.

Validated with 166 passing Python tests and the actual WP1 export.
See [WP4 evidence contract and limitations](16_COBERTURA_PARSER.md).

## D018 - Lexical one-to-one path resolution
**Accepted**

WP5 resolves Cobertura source roots and class filenames against the Git repository
root without opening files, following symlinks, or using a basename fallback. It
normalizes separators and lexical `.` / `..`; paths that escape their root or cannot
be resolved safely supply no mapping candidate.

Only a one-to-one match between one class record and one changed Git path is usable.
Missing candidates and any many-to-one or one-to-many relation stay explicit, so WP6
must classify them as `unknown`. Windows-syntax evidence is case-insensitive; POSIX
syntax remains case-sensitive, independently of the host OS.

See [WP5 path normalization](17_PATH_NORMALIZATION.md).

## D019 - Explicit line-evidence classification
**Accepted**

WP6 maps only changed head lines. A line is covered or uncovered only when one
one-to-one path match yields one explicit class-level record with respectively
positive or zero hits. Missing, unavailable and ambiguous evidence remain `unknown`
with stable reasons; method-level evidence never fills a missing class-level record.

It preserves Git file/hunk/line order in `AnalysisResult` and leaves branch mapping,
exclusions, denominators and rendering for later work packages.

See [WP6 line mapping](18_LINE_MAPPER.md).

## D020 - Aggregate-only branch evidence
**Accepted**

WP7 reports branch coverage only as a collector aggregate at a changed line. A valid
`branch=true` and `condition-coverage` count pair creates a covered/total aggregate;
TC1 does not label any outcome as source-level true or false.

Malformed, contradictory or repeated branch evidence creates an unknown branch result
with a visible reason. No branch result is invented for a line with no collector branch
signal, unmatched paths, or method-only evidence, because those do not identify a
branch candidate safely.

See [WP7 branch mapping](19_BRANCH_MAPPER.md).


## D021 - One shared, outcome-based metric summary
**Accepted**

WP8 calculates line and branch metrics once from mapped evidence and attaches
`AnalysisMetrics` to the immutable `AnalysisResult`; reports must consume that value
rather than independently calculating percentages. A summary always exposes
candidates, classifiable, covered, uncovered, unknown and excluded.

Coverage is `covered / (covered + uncovered)` and is `null` if there is no
classifiable evidence. Unknown and excluded findings remain visible but stay outside
the denominator. A reliable branch aggregate contributes its collector-reported
outcomes; an unknown branch result contributes one unknown finding without claiming a
number of unavailable outcomes. There is currently no branch-exclusion input model.

See [WP8 metrics](20_METRICS.md).

Fill during implementation:
## Pending decisions



```text
Final CLI shape:
HTML renderer choice:
Real pilot repository when available:
Real pilot collector:
CI provider:
Threshold policy:
```


## D022 - Explicit report destinations and ReportGenerator evidence links
**Accepted**

WP9 accepts optional explicit JSON, Markdown and HTML destinations. It renders each requested artifact from one metrics-ready `AnalysisResult` and rejects colliding destinations. ReportGenerator remains a separate supporting visualization: the caller provides its HTML entry page through `--report-generator-html`; TC1 makes an output-relative link when possible and reports its availability without generating, copying or guessing coverage HTML. See [WP9 reports](21_REPORTS.md).


## D023 - Manifest-driven controlled evaluation
**Accepted**

WP10 keeps one reviewed Cobertura fixture, Git-like change manifests and expected public finding/metric outputs under version control. The evaluator invokes the production parser, mapper and metrics code; it compares complete public outputs rather than recreating classification rules. Generated run output belongs under `artifacts/eval/<run-id>/`. Controlled mapping accuracy and the separate human reviewer-time question must not be conflated. See [WP10 evaluation](22_EVALUATION.md).


## D024 - Real-pilot readiness before external integration
**Accepted**

WP11 readiness is documented without accessing or assuming an external repository. A real pilot must be one authorized local C# repository with its existing tests, a reviewed committed diff, valid Cobertura class-level evidence and manual finding observations. Pilot paths, source content, credentials and internal URLs remain outside this repository; generated material stays in approved local artifacts. No CI gate follows from readiness alone. See [real-pilot readiness](23_REAL_PILOT_READINESS.md).
