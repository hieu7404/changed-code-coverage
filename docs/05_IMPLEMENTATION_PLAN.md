# Implementation Plan

## WP0 â€” Bootstrap and local pilot

- read `AGENTS.md`;
- verify Git/Python/.NET;
- create repo structure;
- create controlled C# sample;
- add initial tests;
- confirm `dotnet test`.

Exit:

```text
sample tests pass
```

## WP1 â€” Coverage baseline

- add compatible coverage collection;
- produce coverage export;
- normalize to Cobertura XML;
- run ReportGenerator;
- manually inspect known covered/uncovered locations.

Exit:

```text
artifacts/tc1/coverage.cobertura.xml
+
artifacts/tc1/coverage/ (ReportGenerator HTML)
```

Raw collector exports and test-run results go under `artifacts/test-results/`.

## WP2 â€” Python bootstrap

Create:

```text
src/tc1/
tests/
fixtures/
pyproject.toml
```

Add:
- CLI entry point;
- models;
- pytest;
- errors.

Exit (validated):

```text
editable package install succeeds
tc1 --help / --version work
python -m tc1 uses the same CLI
pytest passes
analyze reports not implemented and writes no artifacts
```

See [WP2 implementation and validation](14_PYTHON_BOOTSTRAP.md).

## WP3 â€” Git diff parser

Use a narrow zero-context diff such as:

```bash
git diff --unified=0 <base>...<head>
```

Support:
- modified files;
- added files;
- multiple hunks;
- multiple files.

Handle explicitly:
- deleted files;
- binary files;
- rename/copy limitations.

Exit (validated): resolved revisions and a unique merge base; deterministic head-line
candidates across files/hunks; visible deleted/binary/type limitations; reviewed
fixtures and real-Git integration tests. Rename/copy detection is disabled explicitly.
See [WP3 implementation and validation](15_GIT_DIFF_PARSER.md).

## WP4 â€” Cobertura parser

Parse:
- filename;
- line;
- hits;
- branch/condition metadata when available.

Do not infer absent data.

Exit (validated): exact class-level line/hit records; method evidence kept separately;
source/branch metadata preserved; malformed inputs rejected; controlled fixtures and
the actual WP1 export checked. See [WP4 implementation](16_COBERTURA_PARSER.md).

## WP5 â€” Path normalization

Normalize:
- slash direction;
- absolute vs relative;
- repo root;
- `.` / `..`.

Reject ambiguous matches.


Exit (validated): Git names and Cobertura source-root/class-filename evidence are
resolved lexically and independently of the host OS. Windows-syntax evidence is
case-insensitive while POSIX evidence remains case-sensitive. One class that names
multiple changed Git paths, or multiple classes that name one Git path, is explicitly
`ambiguous`; unmatched paths remain `unmatched`. No basename fallback is used.

See [WP5 implementation and validation](17_PATH_NORMALIZATION.md).

## WP6 â€” Line mapper

For each changed line:

```text
mapped + hits > 0 â†’ covered
mapped + hits = 0 â†’ uncovered
missing/ambiguous â†’ unknown
```

Exit (validated): each changed head line becomes `covered` only from one explicit
positive-hit class-level entry, and `uncovered` only from one explicit zero-hit entry.
Missing path/line evidence, unavailable files and duplicate evidence remain `unknown`
with visible reasons. Method evidence is never used as a class-line fallback.

See [WP6 implementation and validation](18_LINE_MAPPER.md).

## WP7 â€” Branch mapper

Map changed branch evidence only when reliable.

If only aggregate condition coverage exists, report aggregate state.

Ambiguous branch identity:

```text
unknown
```

Exit (validated): a changed line with reliable `branch=true` aggregate metadata
produces covered/total outcomes without semantic true/false labels. Malformed,
contradictory or duplicate branch evidence stays an unknown `BranchResult`; lines
without a collector branch signal do not become branch candidates.

See [WP7 implementation and validation](19_BRANCH_MAPPER.md).

## WP8 â€” Metrics

Produce separate line and branch summaries:

```text
candidates
classifiable
covered
uncovered
unknown
excluded
coverage_percent
```

Exit (validated): metrics are derived once from mapped evidence and attached to the
shared `AnalysisResult`. Line and branch percentages use only covered plus uncovered
outcomes; unknown and excluded findings remain visible. A zero denominator is `null`,
never `0%`. An unknown branch finding counts as one visible unknown candidate because
its number of outcomes is not known; a reliable aggregate contributes its reported
outcome count.

See [WP8 metrics](20_METRICS.md).

## WP9 â€” Reports

Generate from one shared `AnalysisResult`:

```text
artifacts/tc1/report.json
artifacts/tc1/report.md
artifacts/tc1/index.html
```

Bundle/link ReportGenerator coverage HTML.

Exit (validated): JSON, Markdown and standalone HTML render the same stored metrics and findings from one `AnalysisResult`. The CLI writes explicitly requested, distinct destinations and can link an explicitly supplied ReportGenerator entry page without generating or guessing it. See [WP9 report contract](21_REPORTS.md).

## WP10 â€” Evaluation

Build controlled cases for:
- fully covered;
- partially covered;
- fully uncovered;
- missing instrumentation;
- multiple files;
- multiple hunks;
- new file;
- path mismatch;
- branches;
- ambiguous branches;
- no classifiable evidence.

Commit reviewed cases and expected results under `fixtures/` and `eval/`.
Write generated evaluation results to `artifacts/eval/<run-id>/` and durable findings
to `docs/`, following the [output policy](03_ARCHITECTURE.md#generated-output-policy).

## WP11 â€” Real-pilot readiness

When a real repository becomes available:

- select one existing C# project;
- reuse existing tests;
- select compatible collector;
- run sampled real-diff validation;
- record mapping discrepancies.

Do not change core architecture just because the pilot changes.

## WP12 â€” Optional report-only CI

Only after controlled fixtures pass and sampled diff mappings have been manually validated.
Use real-pilot diffs when available; otherwise document the controlled sample and its
limitations. Follow `AGENTS.md` for the validation sequence.

Pipeline:

```text
test
â†“
coverage
â†“
TC1
â†“
upload artifact
```

No blocking gate.

## WP13 â€” Optional CI gate

Post-MVP only, with explicit user/team approval.

Only after:
- controlled fixtures pass;
- real/sample mappings are validated;
- unknown rate is understood;
- threshold semantics are approved.

Do not invent an arbitrary threshold.

## Handover

Maintain setup, CLI, demo, evaluation, and limitation documentation throughout the work.
Finalize the local MVP handover after WP10 so another developer can reproduce its results.
Optional real-pilot and CI work must not block that handover.
