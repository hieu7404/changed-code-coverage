# WP8 Metrics

## Status

**WP8 complete.** TC1 derives deterministic line and branch summaries from mapped
evidence and attaches them to the shared immutable `AnalysisResult`. WP9 renderers consume these metrics directly; they do not recompute them.

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
the range 0 to 100, or `None` when there is no classifiable evidence. Renderers in [WP9](21_REPORTS.md) format this stored value; they do not recompute it.

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

The combined analysis pipeline creates explicit exclusions from caller-supplied path
rules before coverage mapping. Excluded changed lines remain findings with their
matching rule as the reason; they never enter `classifiable`.

### Branch counts

A reliable `BranchAggregate(covered, total)` contributes `total` branch candidates:
`covered` covered outcomes and `total - covered` uncovered outcomes. An unknown
`BranchResult` contributes one unknown candidate. This visible finding does not claim
that exactly one branch outcome is unavailable; the collector did not provide its
outcome count safely. The current input model has no explicit branch exclusion, so
branch `excluded` is zero. Branches on excluded changed lines are not mapped, because
TC1 cannot determine their reliable outcome count without processing collector
evidence.

This accounting keeps reliable aggregate outcomes in the branch denominator while
preserving unreliable branch evidence without treating it as uncovered.

## Validation

`tests/test_metrics.py` checks line denominator accounting, branch aggregate outcome
accounting, unknown/exclusion visibility, null coverage, immutability, and invalid
summary-count rejection. CLI and renderer tests confirm the same stored metrics reach every output.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_metrics.py -q
.venv/Scripts/python.exe -m pytest
git diff --check
```

## Limitations

- WP8 owns calculation; [WP9 renderers](21_REPORTS.md) consume its stored values.
- Branch unknown counts represent unknown findings, not fabricated counts of source
  outcomes.
- No coverage threshold or CI gate is introduced.

Next bounded step: **WP11 real-pilot readiness**.
