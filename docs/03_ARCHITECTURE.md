# Architecture

## Core principle

The mapper is deterministic.

```text
test execution evidence
+
Git change evidence
â†“
deterministic mapping
```

No LLM is needed for MVP correctness.

## Flow

```text
C# pilot
  â†“
tests
  â†“
coverage collector
  â†“
Cobertura XML
        +
Git base/head
  â†“
git diff
        â†“
path normalization
        â†“
mapping engine
        â†“
covered / uncovered / unknown
        â†“
metrics
        â†“
AnalysisResult
        â†“
JSON / Markdown / HTML
```

## Python modules

```text
src/tc1/
â”œâ”€â”€ __init__.py
â”œâ”€â”€ __main__.py
â”œâ”€â”€ cli.py
â”œâ”€â”€ models.py
â”œâ”€â”€ git_diff.py
â”œâ”€â”€ diff_parser.py
â”œâ”€â”€ cobertura.py
â”œâ”€â”€ path_normalizer.py
â”œâ”€â”€ matcher.py
â”œâ”€â”€ branch_mapper.py
â”œâ”€â”€ metrics.py
â”œâ”€â”€ report_json.py
â”œâ”€â”€ report_markdown.py
â”œâ”€â”€ report_html.py
â””â”€â”€ errors.py
```

### WP8 implementation boundary

The package implements CLI/package entry points, models, errors, Git acquisition
(`git_diff.py`), pure raw/patch parsing (`diff_parser.py`), Cobertura parsing
(`cobertura.py`), lexical path resolution (`path_normalizer.py`), line mapping
(`matcher.py`), and branch mapping (`branch_mapper.py`). Git produces `GitDiffResult`;
XML produces `CoverageReport`; mapping produces `LineResult` and aggregate `BranchResult`
records in one `AnalysisResult`. WP8 derives and attaches one `AnalysisMetrics` value to that same result; future renderers consume it rather than recomputing metrics. Branch aggregates require reliable collector metadata;
no semantic outcome identity is inferred.

Cobertura class-level lines form the primary inventory; method lines remain separate.
Duplicate records, source strings and raw branch metadata are preserved.
Frozen dataclasses provide evidence and result records for one shared `AnalysisResult`.
Report rendering remains WP9.
See [WP2 models](14_PYTHON_BOOTSTRAP.md), [Git comparison](15_GIT_DIFF_PARSER.md),
and [WP7 branch mapping](19_BRANCH_MAPPER.md).

## Classification rules

### Covered
Explicit coverage entry shows execution.

For a line:

```text
hits > 0
```

### Uncovered
Explicit instrumentation exists and shows no execution.

For a line:

```text
hits == 0
```

### Unknown
Evidence is missing or unreliable.

Examples:
- source file absent from coverage;
- changed line not instrumented;
- ambiguous path;
- branch metadata cannot be mapped safely.

Rule:

```text
missing evidence != uncovered
```

## Branch handling

Branch reporting is part of the target MVP only where reliable evidence exists.

If export provides only:

```text
condition coverage = 50% (1/2)
```

report that aggregate state rather than inventing which semantic path was missed.

## Metrics

Line:

```text
covered / (covered + uncovered)
```

Branch:

```text
covered / (covered + uncovered)
```

Unknown/excluded items remain visible but are outside the denominator.

If the denominator is zero, coverage is `null` / not applicable, not `0%`.

## ReportGenerator

ReportGenerator is supporting visualization.

The Python mapper owns TC1-specific changed-code mapping.

Recommended artifact:

```text
artifacts/tc1/
â”œâ”€â”€ report.json
â”œâ”€â”€ report.md
â”œâ”€â”€ index.html
â”œâ”€â”€ coverage.cobertura.xml
â””â”€â”€ coverage/
    â””â”€â”€ ReportGenerator HTML
```

## Generated output policy

All generated reports, coverage exports, test-run logs/results, and evaluation results
go under the repository-root `artifacts/`, regardless of size. This directory is gitignored.
Paths below are relative to the repository root; commands run elsewhere must resolve them
against that root.

| Location | Contents |
| --- | --- |
| `artifacts/tc1/` | TC1 reports and the normalized Cobertura input bundled with them |
| `artifacts/tc1/coverage/` | ReportGenerator coverage HTML |
| `artifacts/test-results/` | Raw collector exports, test-run results and logs |
| `artifacts/eval/<run-id>/` | Evaluation results and run metadata |

Configure test runners and collectors to write to these locations. Normalize or copy the
selected coverage export to `artifacts/tc1/coverage.cobertura.xml` for the report bundle.
Build intermediates and tool caches may keep their standard gitignored locations
(`bin/`, `obj/`, `.pytest_cache/`, etc.).

Small reviewed deterministic inputs and expected results are committed under `fixtures/`
and `eval/`; they are maintained test assets, not automatically saved run output.
Durable methodology, decisions, and evaluation summaries belong in `docs/` and reference
the generated artifacts with reproduction instructions.
