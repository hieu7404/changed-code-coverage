# Evaluation Plan

## Goal 1 — Technical correctness

Use controlled fixtures with known ground truth.

Recommended scenarios:

```text
E01 fully covered lines
E02 partial line coverage
E03 fully uncovered lines
E04 missing line instrumentation
E05 multiple files
E06 multiple hunks
E07 new file
E08 deleted file
E09 path normalization
E10 fully covered branch
E11 partially covered branch
E12 branch metadata ambiguous/missing
E13 no classifiable changed code
E14 multiple coverage classes for one source file
```

## Metrics

```text
line_candidates
line_correct
line_incorrect
line_mapping_accuracy

branch_candidates
branch_correct
branch_incorrect
branch_mapping_accuracy

unknown_count
excluded_count
ambiguous_mapping_count
```

Controlled deterministic fixtures target:

```text
100% expected classification
```

If controlled fixtures fail, fix the mapping logic instead of hiding errors in averages.

## Goal 2 — Research usefulness

Question:

> Does a changed-code report help reviewers find relevant test gaps faster than repository-wide coverage alone?

### Baseline
Reviewer sees overall coverage and normal source/diff.

### TC1
Reviewer additionally sees changed-code findings.

Measure:
- time to locate gaps;
- correct gaps found;
- missed gaps;
- incorrect conclusions.

## Unknown and denominator reporting

Always show:

```text
covered
uncovered
unknown
excluded
classifiable denominator
```

Do not hide unknowns because they are excluded from coverage percentage.

## Evaluation storage

Commit reviewed evaluation manifests and expected results under `eval/`, with reusable
inputs under `fixtures/`. Save all generated evaluation results and run metadata under
`artifacts/eval/<run-id>/`. Keep durable evaluation summaries in `docs/`.
See [Generated output policy](03_ARCHITECTURE.md#generated-output-policy).

## Real repository validation later

When real access exists:

1. sample a small number of real diffs;
2. manually inspect mappings;
3. record false mappings/unknowns;
4. identify causes;
5. only then consider CI gating.
