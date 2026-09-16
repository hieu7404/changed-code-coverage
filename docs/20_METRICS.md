# WP8 Metrics

## Status

**WP8 complete.** TC1 derives deterministic line and branch summaries from mapped
evidence and attaches them to the shared immutable `AnalysisResult`. The CLI computes
these metrics before stopping at the still-unimplemented WP9 reporting boundary.

## API

```python
from tc1.metrics import attach_metrics, calculate_metrics

metrics = calculate_metrics(mapped_analysis)
analysis = attach_metrics(mapped_analysis)
assert analysis.metrics == metrics
```

`CoverageSummary` has these fields:

```text
candidates
classifiable
covered
uncovered
unknown
excluded
coverage_percent
```

`coverage_percent` is derived, never supplied independently. It is a percentage in
the range 0 to 100, or `None` when there is no classifiable evidence. Renderers in
WP9 must format this stored value; they must not recompute it.

## Denominator contract

For both lines and branches:

```text
classifiable = covered + uncovered
coverage_percent = 100 * covered / classifiable
```

A zero `classifiable` count produces `coverage_percent = None`, not `0%`.
Unknown and excluded evidence is visible in the summary but excluded from the
percentage denominator.

### Line counts

Every `LineResult` is one candidate. Its status increments exactly one of covered,
uncovered, or unknown. Every explicit `ExcludedLine` is one excluded candidate.
Consequently:

```text
candidates = classifiable + unknown + excluded
```

### Branch counts

A reliable `BranchAggregate(covered, total)` contributes `total` branch candidates:
`covered` covered outcomes and `total - covered` uncovered outcomes. An unknown
`BranchResult` contributes one unknown candidate. This visible finding does not claim
that exactly one branch outcome is unavailable; the collector did not provide its
outcome count safely. The current input model has no explicit branch exclusion, so
branch `excluded` is zero.

This accounting keeps reliable aggregate outcomes in the branch denominator while
preserving unreliable branch evidence without treating it as uncovered.

## Validation

`tests/test_metrics.py` checks line denominator accounting, branch aggregate outcome
accounting, unknown/exclusion visibility, null coverage, immutability, and invalid
summary-count rejection. CLI tests confirm metrics run before the WP9 stop boundary.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_metrics.py -q
.venv/Scripts/python.exe -m pytest
git diff --check
```

## Limitations

- WP8 does not write JSON, Markdown, or HTML; that is WP9.
- Branch unknown counts represent unknown findings, not fabricated counts of source
  outcomes.
- No coverage threshold or CI gate is introduced.

Next bounded step: **WP9 reports**.