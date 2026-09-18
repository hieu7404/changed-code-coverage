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
| One explicit entry at the changed line across all matched classes, hits > 0 | `covered` | `explicit_positive_hits` |
| One explicit entry at the changed line across all matched classes, hits = 0 | `uncovered` | `explicit_zero_hits` |
| No matching path | `unknown` | `path_unmatched` |
| Ambiguous path | `unknown` | `path_ambiguous` |
| No primary class line inventory | `unknown` | `class_has_no_primary_line_evidence` |
| No explicit entry at the changed line | `unknown` | `no_explicit_line_evidence` |
| Repeated entry at the changed line | `unknown` | `ambiguous_line_evidence` |
| Git file is unavailable | `unknown` | `file_unavailable:<reason>` |

Multiple Cobertura classes may name one source file, as happens with compiler-generated
async/iterator state machines. The mapper considers all their primary line inventories
but requires exactly one entry at the changed line. Method-level records are never
substituted for missing class-level evidence. Repeated same-line records are not
deduplicated, even when their hit counts agree. This preserves the rule that missing
or unreliable evidence is not uncovered.

## Explicit path exclusions

The combined pipeline accepts ordered, repository-relative path globs:

```python
analysis = map_changed_code(
    git_diff_result,
    coverage_report,
    exclude_paths=("**/*.g.cs", "vendor/**"),
)
```

TC1 applies these rules before both line and branch mapping. Every changed head line
in a matching file becomes an `ExcludedLine` with reason `path_rule:<pattern>`; it is
not also reported as covered, uncovered or unknown. The first matching pattern wins.
Patterns are case-sensitive, normalize `\` to `/`, and support `*` and `?` within one
path segment plus `**` across segments. Absolute and parent-escaping patterns fail as
invalid input. TC1 supplies no default exclusion rules.

Because the collector identifies branch candidates only during mapping, branches on
an excluded changed line are not mapped or counted. TC1 does not invent an excluded
branch count from source text.

## Validation

```powershell
.venv/Scripts/python.exe -m pytest tests/test_matcher.py -q
.venv/Scripts/python.exe -m pytest
git diff --check
```

Focused cases cover covered, uncovered, missing, unmatched, ambiguous, same-file
compiler-generated classes, duplicate same-line records, method-only and
unavailable-file evidence, Git result order, portable glob semantics, first-rule
selection, invalid patterns, and exclusion before line/branch mapping.

## Limitations

- Exclusions currently come from repeatable CLI arguments or the Python API; a
  project configuration file is not implemented.
- Rules apply to whole files, not individual line ranges or source syntax categories.
- TC1 does not infer generated code, test code or other policy-specific exclusions.
