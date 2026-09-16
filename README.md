# TC1 — Changed-Code Coverage Analyzer

TC1 is a small software-engineering/research side project that measures **coverage on changed code**, rather than relying only on repository-wide coverage.

## Core question

> What code changed, and did the current test suite actually exercise that changed code?

## Basic flow

```text
Git diff
→ changed code

Coverage export
→ executed code

Git diff + coverage
→ TC1 mapper
→ covered / uncovered / unknown
```

## Why this matters

A repository can have:

```text
Overall coverage:      85%
Changed-code coverage: 30%
```

The overall number may look healthy while the current change is poorly protected by tests.

## MVP stack

- Python 3.11+ for the TC1 mapper
- one C#/.NET pilot
- existing C# test runner
- Coverlet when compatible
- Cobertura XML
- ReportGenerator
- pytest
- Git CLI

## Portable setup

This repository is standalone.

It does **not** depend on:
- a specific Windows username/path;
- a DMS workspace;
- company network access;
- AI APIs;
- external datasets;
- downloaded models.

The first local pilot can be a small controlled C# sample. A real company C# project can be integrated later without changing the TC1 architecture.

## Read first

1. `AGENTS.md`
2. `docs/00_START_HERE.md`
3. `docs/01_PROJECT_BRIEF.md`
4. `docs/04_ENVIRONMENT_SETUP.md`
5. `docs/05_IMPLEMENTATION_PLAN.md`
6. `docs/06_TASK_CHECKLIST.md`

## MVP result

Expected artifact:

```text
Changed-Code Coverage

Lines
  candidates:   20
  classifiable: 15
  covered:      10
  uncovered:     5
  unknown:       3
  excluded:      2
  coverage:     66.67%

Branches
  candidates:    4
  classifiable:  3
  covered:       2
  uncovered:     1
  unknown:       1
  coverage:     66.67%
```

## Current implementation

WP0-WP7 are complete: the C# sample has a validated coverage baseline, and the Python
tool reads Git changes and Cobertura evidence, resolves paths without guessing file
identity, and maps changed lines and reliable branch aggregates. Metrics and reports remain WP8-WP9.
See [Python setup](docs/14_PYTHON_BOOTSTRAP.md),
[Git diff](docs/15_GIT_DIFF_PARSER.md), and
[Cobertura and current CLI behavior](docs/16_COBERTURA_PARSER.md), and
[path normalization](docs/17_PATH_NORMALIZATION.md), and
[line mapping](docs/18_LINE_MAPPER.md), and
[branch mapping](docs/19_BRANCH_MAPPER.md).

## Important scope rule

The MVP is **not** an AI code-review agent.

Build the deterministic coverage mapper first. AI-related extensions can be considered only after MVP validation.
