# WP7 Branch Mapper

## Status

**WP7 complete.** The mapper reports only reliable aggregate branch evidence at
changed head lines. It never assigns coverage to semantic true/false paths.

## API

```python
from tc1.matcher import map_changed_code

analysis = map_changed_code(git_diff_result, coverage_report)
```

The shared `AnalysisResult` contains the completed line findings and `branches`.
A `BranchResult` has a location, reason and either an aggregate (`covered`, `total`)
or `None` for unknown evidence.

## Branch contract

A branch result is considered only for a changed line with class-level branch signal.
A reliable result requires an unambiguous file-path match, exactly one class-level
record at the changed line across all matched classes, `branch="true"`, and a
`condition-coverage` aggregate in this shape:

```text
<percentage>% (<covered>/<total>)
```

The parenthesized counts become `BranchAggregate`; the percentage is retained only as
collector display metadata. For example, `50% (1/2)` becomes `BranchAggregate(1, 2)`.
No source text is read and no outcome is labelled true or false.

| Evidence | Branch result |
| --- | --- |
| `branch=true`, valid aggregate | Aggregate with `aggregate_condition_coverage` |
| `branch=true`, missing/malformed aggregate | Unknown: `branch_aggregate_unreliable` |
| `branch=false`, no condition data | No branch candidate |
| `branch=false` plus condition data | Unknown: `branch_metadata_contradictory` |
| Repeated evidence at one changed line | Unknown: `ambiguous_branch_line_evidence` |
| Unavailable changed file | Unknown: `file_unavailable:<reason>` |

An unmatched path, method-only evidence, or a changed line with no branch signal does
not establish a branch candidate and produces no `BranchResult`. This avoids inflating
the branch denominator from source lines that cannot be known to contain a branch.

## Historical CLI boundary

At WP7, `tc1 analyze` mapped changed lines and reliable branch aggregates, then
stopped before metrics and report rendering. The current CLI writes WP9 reports; see
[the report contract](21_REPORTS.md).

## Validation

```powershell
.venv/Scripts/python.exe -m pytest tests/test_branch_mapper.py -q
.venv/Scripts/python.exe -m pytest
git diff --check
```

Focused cases cover full, partial and zero aggregate coverage; malformed/contradictory
metadata; multiple compiler-generated classes for one file; duplicate same-line
records; method-only/unmatched evidence; unavailable files; and Git result ordering.

## Limitations

- Branch candidates are collector-evidence-based, not source-syntax-based.
- Report rendering is defined in [WP9](21_REPORTS.md); denominator semantics are defined in [WP8 metrics](20_METRICS.md).

Next bounded step: **WP11 real-pilot readiness**.
