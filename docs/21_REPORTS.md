# WP9 Reports

## Status

**WP9 complete.** TC1 renders JSON, Markdown and standalone HTML from the same
metrics-ready `AnalysisResult`. Renderers display the metrics already attached by
WP8; they do not recalculate classifications, denominators or percentages.

## CLI

`tc1 analyze` accepts any combination of these optional destinations:

```text
--json <path>
--markdown <path>
--html <path>
```

It also accepts repeatable, repository-relative path exclusions:

```text
--exclude-path "**/*.g.cs"
--exclude-path "**/*.Designer.cs"
--exclude-path "vendor/**"
```

Rules are explicit per invocation; TC1 has no implicit project-specific exclusions.
They support `*`, `?` and `**`, use `/` as the normalized separator, and are matched
case-sensitively against Git paths. Each excluded changed head line remains in the
report with `path_rule:<pattern>` as its reason and stays outside the denominator.

No destination means TC1 validates and maps the requested evidence without writing a
report. Every supplied parent directory is created. Destinations must be distinct;
TC1 rejects a collision before writing anything. Output paths are resolved relative
to the caller's working directory, like the coverage input.

To link an already-generated ReportGenerator bundle, pass its entry page explicitly:

```powershell
tc1 analyze `
  --repo . `
  --base <base-commit> `
  --head HEAD `
  --coverage artifacts/tc1/coverage.cobertura.xml `
  --json artifacts/tc1/report.json `
  --markdown artifacts/tc1/report.md `
  --html artifacts/tc1/index.html `
  --report-generator-html artifacts/tc1/coverage/index.html
```

TC1 does not invoke or copy ReportGenerator. That tool remains responsible for its
own coverage visualization. For each requested TC1 output, the supplied evidence path
is made relative to that output when possible. If the file is absent, the report keeps
the expected path and marks it unavailable; it is never silently replaced with a
different file.

## Output contract

`report.json` uses schema version `1.0` and contains:

- resolved `analysis.base` and `analysis.head` commits;
- line and branch metrics with all visible counts and `coverage_percent` (`null` when
  not applicable);
- line, exclusion and aggregate-branch findings in mapper order;
- optional ReportGenerator supporting-evidence path and availability.

Markdown and HTML contain the same line/branch summaries and findings. The HTML is a
standalone, UTF-8 document and escapes evidence-derived text. Markdown escapes table
separators and line breaks. Branch output is aggregate-only: `covered / total` where
the collector proves it, otherwise `unknown`; no true/false identity is inferred.

## Validation

`tests/test_reports.py` covers deterministic JSON, shared metrics, null denominators,
branch aggregates and text escaping. `tests/test_cli.py` covers all three outputs,
ReportGenerator linking/unavailability, output collisions and existing input failures.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_reports.py tests/test_cli.py -q
.venv/Scripts/python.exe -m pytest
git diff --check
```

## Limitations

- TC1 reports only evidence already produced by the collector and mapper.
- A missing ReportGenerator page is reported as unavailable; TC1 does not generate it.
- Output writes are individual files; WP9 does not provide a multi-file transaction.
- Project configuration files are not yet supported; repeat CLI options define the
  exclusion policy for each invocation.
- No coverage threshold or CI gate is introduced.

Next bounded step: **WP11 real-pilot readiness**.
