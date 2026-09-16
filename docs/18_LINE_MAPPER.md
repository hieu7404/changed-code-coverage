# WP6 Line Mapper

## Status

**WP6 complete.** The mapper classifies each changed head line only from explicit,
reliable class-level Cobertura evidence. It returns the shared `AnalysisResult` and
does not calculate metrics, map branches, or create reports.

## API

```python
from tc1.matcher import map_changed_lines

analysis = map_changed_lines(git_diff_result, coverage_report)
```

`analysis.lines` follows Git file/hunk/head-line order. Each finding includes the Git
path and line, a status, a machine-stable reason, and hits only where evidence is
explicit and reliable.

## Classification contract

| Evidence | Status | Reason |
| --- | --- | --- |
| One matched class-level entry, hits > 0 | `covered` | `explicit_positive_hits` |
| One matched class-level entry, hits = 0 | `uncovered` | `explicit_zero_hits` |
| No matching path | `unknown` | `path_unmatched` |
| Ambiguous path | `unknown` | `path_ambiguous` |
| No primary class line inventory | `unknown` | `class_has_no_primary_line_evidence` |
| No explicit entry at the changed line | `unknown` | `no_explicit_line_evidence` |
| Repeated entry at the changed line | `unknown` | `ambiguous_line_evidence` |
| Git file is unavailable | `unknown` | `file_unavailable:<reason>` |

Method-level Cobertura records are never substituted for missing class-level evidence.
Repeated records are not deduplicated, even when their hit counts agree. This preserves
the rule that missing or unreliable evidence is not uncovered.

## Historical CLI boundary

`tc1 analyze` now resolves Git, parses Cobertura and maps changed lines before it stops
with an explicit WP7-WP9 error. The message includes raw input counts and the number of
line results. No report output is written or overwritten.

## Validation

```powershell
.venv/Scripts/python.exe -m pytest tests/test_matcher.py -q
.venv/Scripts/python.exe -m pytest
git diff --check
```

Focused cases cover covered, uncovered, missing, unmatched, ambiguous, duplicate,
method-only and unavailable-file evidence, plus Git result order.

## Limitations

- Exclusions and percentages remain WP8.
- Branch evidence remains raw until WP7.
- The CLI intentionally exposes no line-result report until WP9.

Next bounded step: **WP7 branch mapper**.
