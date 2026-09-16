# WP10 Controlled Evaluation

## Status

The deterministic controlled evaluation is complete. All 13 reviewed scenarios pass
through the production Cobertura parser, path resolver, line/branch mapper and WP8
metrics. The suite does not substitute synthetic expected values for production mapping
logic.

The separate reviewer-time pilot is prepared but not executed: it requires human
reviewers and a baseline comparison, so it remains pending rather than being inferred
from automated results.

## Reproduce

Run from the repository root after installing the editable Python package:

```powershell
.venv/Scripts/python.exe eval/run_eval.py --run-id controlled
```

The runner writes `artifacts/eval/controlled/results.json`. Use a distinct run ID when
preserving several runs. Its committed inputs are:

```text
eval/cases/controlled.json
fixtures/evaluation/controlled.xml
eval/expected/controlled.json
```

`results.json` preserves the actual and reviewed expected public finding/metric shape
per case, plus the aggregate accuracy summary. A non-zero exit means at least one case
differs from its reviewed expectation.

## Controlled scenarios

| IDs | Evidence under test |
| --- | --- |
| E01–E03 | Fully covered, partial and fully uncovered changed lines |
| E04 | Missing explicit line evidence remains `unknown` |
| E05–E06 | Multiple files and multiple hunks preserve mapping order |
| E07–E08 | Added file and deleted-file/no-head-line handling |
| E09 | Windows-style Cobertura path normalization |
| E10–E11 | Fully and partially covered reliable branch aggregates |
| E12 | Missing branch aggregate remains `unknown` |
| E13 | Ambiguous and unmatched paths remain `unknown` with no denominator entry |

E03 mirrors the manual E2E sample result: a committed change to the intentionally
untested 20% discount return mapped to `uncovered`, with zero hits.

## Result

The initial controlled run passed all 13 cases:

| Metric | Value |
| --- | ---: |
| Line candidates / correct / incorrect | 16 / 16 / 0 |
| Line mapping accuracy | 100.0% |
| Branch findings / correct / incorrect | 3 / 3 / 0 |
| Branch mapping accuracy | 100.0% |
| Visible unknown findings | 4 |
| Excluded findings | 0 |
| Ambiguous mapping findings | 1 |

Accuracy counts one reviewed changed-line finding and one reviewed branch finding per
location. Reliable branch outcome totals remain in each case's WP8 branch metrics;
the evaluator compares the complete public branch finding, including its aggregate.
An unexpected or missing finding is incorrect. A zero-candidate category reports
`null`, not 0%.

## Reviewer-time pilot protocol

Use the prepared [reviewer pilot protocol](../eval/reviewer_pilot.md) only with
voluntary participants and a chosen representative diff set. Record aggregate timing,
correct gaps found, missed gaps and incorrect conclusions. Do not treat the controlled
suite's 100% result as evidence of reviewer productivity or real-repository accuracy.

## Limitations and next step

- The controlled cases are synthetic C#-like paths and one validated Cobertura profile.
- They validate deterministic mapping semantics, not collector compatibility in an
  arbitrary external repository.
- No human reviewer-time pilot or real-pilot sample has been run yet.

Next bounded step: **WP11 real-pilot readiness**, once a suitable local C# repository
is available. The reviewer-time pilot may run later without changing the mapper.