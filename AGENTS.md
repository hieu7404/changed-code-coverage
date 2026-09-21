# AGENTS.md — TC1 Standalone Side Project

This file is the primary operating contract for Codex/Cursor/other coding agents working in this repository.

The repository is intentionally **standalone and portable**. Do not assume access to any external DMS/VinFast workspace, absolute Windows path, company network, cloud environment, or private repository unless the user explicitly provides it in the current task.

## 1. Project purpose

TC1 builds a **Changed-Code Coverage Analyzer**.

Core question:

> Of the executable code changed between two Git revisions, which changed lines and branches were exercised by tests, which were not, and which cannot be determined reliably from the available coverage evidence?

Core flow:

```text
Git diff
+
coverage export
↓
deterministic mapper
↓
covered / uncovered / unknown
↓
JSON + Markdown + HTML report
```

The local end-to-end analyzer is implemented and usable for coverage review.
Current documentation starts at `docs/00_START_HERE.md`; delivery status is in
`docs/03_TASK_CHECKLIST.md`. No CI workflow or blocking gate is implemented, and a
trustworthy threshold policy remains unresolved. Do not restart completed MVP work.

## 2. Authority order

When instructions conflict, use this order:

1. User's current explicit request.
2. This `AGENTS.md`.
3. Documents under `docs/`.
4. Existing repository conventions and tests.
5. Reasonable implementation defaults.

If a conflict remains material, preserve scope and document the assumption instead of expanding work.

## 3. Repository boundary

By default:

- Work **inside this repository only**.
- Use relative paths.
- Do not assume any absolute path such as `C:\Users\...`.
- Do not scan sibling folders or the user's home directory.
- Do not modify external repositories unless the user explicitly asks.
- External repositories and public projects are reference-only unless copied/cloned into a clearly designated local reference area.

If the user later connects a real company repository, treat it as a new pilot integration and reassess scope.

## 4. Expected repository layout

Target structure:

```text
.
├── AGENTS.md
├── README.md
├── .gitignore
├── docs/
├── src/
│   └── tc1/
├── tests/
├── fixtures/
├── sample-dotnet/
├── eval/
└── artifacts/          # generated; not committed
```

Agents may create missing implementation folders when the active task reaches that phase.

## 5. Source-of-truth routing

Use:

```text
docs/          durable design, decisions, runbooks, evaluation notes
src/           TC1 Python implementation
tests/         automated tests for TC1
fixtures/      small committed deterministic test fixtures
sample-dotnet/ local controlled C# pilot/sample
eval/          reproducible evaluation manifests and runner
artifacts/     generated reports/coverage/output; gitignored
```

Do not place generated bulky output in `docs/`.

## 6. MVP scope

MVP includes:

- one C#/.NET pilot;
- existing test runner;
- coverage collection;
- normalized Cobertura XML;
- Git base/head diff;
- changed-line mapping;
- changed-branch mapping when reliable evidence exists;
- `covered`, `uncovered`, `unknown`;
- explicit exclusions and denominators;
- JSON report;
- Markdown report;
- HTML artifact;
- ReportGenerator coverage HTML as supporting evidence;
- deterministic fixtures and evaluation;
- optional report-only CI.

## 7. Explicitly out of scope before MVP completion

Do not add without explicit user approval:

- LLMs;
- OpenAI/Anthropic APIs;
- AI agents;
- Graft runtime integration;
- OpenCodeReview runtime integration;
- dependency graphs;
- blast-radius analysis;
- risk scoring;
- web frontend/dashboard;
- database;
- vector database;
- embeddings;
- model downloads/training;
- crawling/scraping;
- multi-language support;
- mutation testing;
- blocking CI gates.

Useful ideas belong in `docs/06_FUTURE_WORK.md`.

## 8. Deterministic evidence rules

Coverage facts must come from instrumentation.

For changed lines:

```text
explicit coverage entry with hits > 0  → covered
explicit coverage entry with hits = 0  → uncovered
missing / ambiguous / unreliable data  → unknown
```

Never convert `unknown` to `uncovered`.

For branches:

- map only when the collector/export provides sufficiently reliable branch evidence;
- if only aggregate condition coverage is available, report the aggregate;
- do not invent semantic true/false identity from source text alone;
- ambiguous mapping → `unknown`.

## 9. Denominator rules

Changed line coverage:

```text
covered_lines / (covered_lines + uncovered_lines)
```

Changed branch coverage:

```text
covered_branches / (covered_branches + uncovered_branches)
```

Unknown/excluded items are not in the denominator but must remain visible in reports.

If there is no classifiable evidence, report coverage as `null` / not applicable, not `0%`.

## 10. Technology defaults

Preferred initial stack:

```text
TC1 tool:        Python 3.11+
Target pilot:    C#/.NET
Testing:         existing C# runner (xUnit/NUnit/MSTest/etc.)
Coverage:        Coverlet when compatible
Normalized data: Cobertura XML
Visualization:   ReportGenerator
Python tests:    pytest
Git access:      git CLI via subprocess
```

For a legacy or incompatible C# project, choose a supported coverage collector and normalize its export before mapping.

Do not replace an existing test framework just to make TC1 easier.

## 11. Search and exploration rules

Before broad exploration:

1. read `README.md`;
2. read `docs/00_START_HERE.md`;
3. read the document relevant to the current task;
4. inspect only the smallest necessary code/path scope.

Prefer exact file discovery and narrow search.

Do not crawl the web or scan unrelated local folders.

## 12. Implementation rules

Prefer:

- small modules;
- explicit data models;
- pure/deterministic logic where possible;
- unit tests with every core module;
- reproducible fixtures;
- clear error handling;
- one shared `AnalysisResult` for all renderers.

Avoid:

- giant scripts;
- hidden fallbacks;
- guessing file mappings;
- silently dropping evidence;
- independent metric calculations in each reporter.

## 13. CI rule

Required sequence:

```text
local deterministic tool
↓
controlled fixture validation
↓
sampled real-diff/manual validation
↓
report-only CI artifact
↓
optional blocking gate
```

Do not create a blocking gate until mapping accuracy has been validated and the user/team explicitly chooses threshold semantics.

Do not invent a default threshold.

## 14. Generated artifacts

Generated output belongs under:

```text
artifacts/
```

Recommended bundle:

```text
artifacts/tc1/
├── report.json
├── report.md
├── index.html
├── coverage.cobertura.xml
└── coverage/
    └── ReportGenerator output
```

`artifacts/` is not source-of-truth documentation.

## 15. Validation expectations

For implementation changes, run the narrowest relevant checks.

Typical checks:

```text
Python:
pytest

Git:
git diff --check
git status --short

C# sample/pilot:
dotnet build
dotnet test

Docs:
check Markdown rendering/links where tooling exists
```

Do not invent repo-wide commands that do not exist.

## 16. Documentation maintenance

Update durable docs when implementation changes affect:

- architecture;
- CLI contract;
- coverage semantics;
- branch support;
- evaluation methodology;
- artifact layout;
- known limitations;
- important decisions.

Record durable decisions in `docs/05_DECISION_LOG.md`.

## 17. Handoff format

At the end of a meaningful implementation step, report:

```text
Scope
Changed files
Validation performed
Result
Known limitations
Next bounded step
```

Keep handoffs concise and evidence-based.
