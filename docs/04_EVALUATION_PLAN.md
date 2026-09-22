# Validation evidence and pilot procedure

TC1's local pipeline and controlled mapping suite are implemented. Controlled
correctness, compatibility with a collector, and usefulness to reviewers are
separate questions; none establishes a trustworthy CI threshold by itself.

## Reproduce automated checks

After the [Python setup](01_DEMO_RUNBOOK.md#1-install), run from the repository root:

```bash
python -m pytest
python eval/run_eval.py --run-id controlled
git diff --check
```

The evaluator writes `artifacts/eval/controlled/results.json`; choose a different
run ID to preserve another run. It uses the production parser, path resolver,
mapper and metrics, comparing complete public findings against reviewed expected
results. A mismatch returns nonzero. That exit status validates the tool's fixtures;
it is not a coverage gate for application code.

## Controlled evaluation

Inputs: [case manifest](../eval/cases/controlled.json),
[Cobertura fixture](../fixtures/evaluation/controlled.xml), and
[expected results](../eval/expected/controlled.json).

| Cases | Evidence tested |
| --- | --- |
| E01–E03 | Fully covered, partially covered and uncovered lines |
| E04 | Missing line instrumentation stays unknown |
| E05–E06 | Multiple files and hunks |
| E07–E08 | Added file and deleted-file/no-head-line behavior |
| E09 | Windows-style path normalization |
| E10–E11 | Full and partial branch aggregates |
| E12 | Missing branch aggregate stays unknown |
| E13 | Duplicate line evidence and unmatched paths stay unknown |
| E14 | Multiple classes resolve unique evidence at each changed line |

The reviewed suite has 14 passing cases: 18/18 line findings and 3/3 branch findings
correct, with 4 visible unknown findings, no exclusions and 1 ambiguous finding.
These accuracy counts compare findings per location; branch outcome denominators
remain separate in each case's coverage metrics. Missing or unexpected findings
are incorrect, and empty accuracy categories are `null`.

The suite uses controlled change inventories, not live Git acquisition. The pytest
suite separately exercises real temporary Git repositories, parsing, exclusions,
CLI behavior and report consistency. No broad real-repository accuracy or reviewer
productivity claim follows from the controlled suite's 100% result.

## Recorded C# baseline

The original Windows sample run used SDK 10.0.401, Coverlet 6.0.4 and ReportGenerator
5.5.11. Seven xUnit tests passed. Manual XML/HTML review found 10/12 instrumented
lines and 5/6 branch outcomes covered (83.33% each). These are whole-sample metrics,
not changed-code percentages or recommended thresholds.

The original source was commit `4400849`; run ID
`wp1-cf63f6c6500d4b6f878108c168eeb6ca` identifies its local ignored metadata and
manual review. Generated evidence is not shipped with a fresh checkout; reproduce
collection using the runbook. The current sample's bulk factor is `0.75m`, changed
from the original `0.80m`. The recorded baseline remains a historical observation.

At the baseline, the bulk-block brace and return (lines 14 and 16) had zero hits;
line 13 had positive hits but only 1/2 branch outcomes covered. The return at line
21 was covered. This demonstrates why line and branch results differ and why
instrumented braces cannot be discarded based on appearance.

A recorded local end-to-end check changed the untested return in commit `e8397f9`
and mapped it to uncovered with zero hits. This is a controlled sample observation,
not representative production-diff validation.

## Preliminary public compatibility observation

A previously authorized local `ardalis/GuardClauses` pilot used existing .NET 8
xUnit tests and Coverlet: 959 tests passed, with class-level evidence for 60 classes.
Its first selected diff had 21 changed head lines: 20 test lines were unmatched
because the test assembly was excluded, and production line 1 lacked instrumentation.
Those lines correctly remained unknown.

That export exposed multiple classes for one source file, including an async state
machine. The resolver now accepts the shared file identity while still requiring
unique evidence per changed line. A diagnostic found 12 hits on line 30, but that
line was outside the selected diff. This proves an observed compatibility case,
not completion of representative classifiable-diff validation. These pilot artifacts
remain local and are not required to run TC1.

## Real-pilot validation

1. Choose an authorized local C# repository with its existing test runner and a
   small set of reviewable committed base/head diffs. Required history must be local.
2. Collect Cobertura from each selected head after tests pass. Record collector,
revision and run metadata; retain the original export. Use a provenance sidecar with
the head commit, clean-worktree state and XML SHA-256, then run TC1 with
`--provenance ... --require-provenance`. Inspect class-level paths, line hits and
branch aggregates before relying on them.
3. Generate reports with the [runbook](01_DEMO_RUNBOOK.md#another-local-c-repository).
4. Compare changed head lines, XML/ReportGenerator and TC1 findings. Sample covered,
   uncovered and unknown cases, exclusions when used, and reliable branch aggregates.
5. Save observations in a local copy of the
   [pilot manifest](../eval/real_pilot_manifest.template.json) under an ignored
   `artifacts/eval/<run-id>/` directory. Classify each observation as match, mapping
   discrepancy, coverage provenance issue, or collector/path limitation.

Verify line identity, hit counts, unknown reasons, explicit exclusion rules, branch
counts and agreement across all three reports. Record sampled diff/finding counts,
unknown rates and discrepancy causes. Keep private source, machine paths and internal
URLs out of committed documentation.

Real-pilot validation remains pending until representative classifiable diffs and
manual observations are recorded. The next integration option is report-only CI;
a gate additionally needs an approved, evidence-based threshold policy.

## Reviewer usefulness

The [reviewer-time protocol](../eval/reviewer_pilot.md) is prepared but has not run.
It compares ordinary diff/overall-coverage review with review assisted by TC1,
recording time, correct gaps, missed gaps and incorrect conclusions. It requires
voluntary human participants; automated tests cannot substitute for those results.
