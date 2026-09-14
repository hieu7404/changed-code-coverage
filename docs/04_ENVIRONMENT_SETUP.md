# Environment Setup

## Goal

Prepare a machine-independent local development environment for TC1.

## Required tools

### Git
Verify:

```bash
git --version
```

### Python
Recommended:

```text
Python 3.11+
```

Verify:

```bash
python --version
```

### .NET SDK
Install a currently supported .NET SDK suitable for the local sample.

Verify:

```bash
dotnet --info
```

### Coverage tool
Preferred initial choice:

```text
Coverlet
```

Use another supported collector if the selected pilot is incompatible.

### ReportGenerator
Use it to render canonical coverage HTML.

## Python virtual environment

Example:

```bash
python -m venv .venv
```

Activate it using the command appropriate for the local shell.

Later, when `pyproject.toml` exists, install the project in editable mode.

## Local sample strategy

Create a small C# sample in:

```text
sample-dotnet/
```

Recommended sample domain:

```text
CalculatorService
DiscountService
OrderService
```

Include multiple if/else branches and intentionally incomplete tests.

Purpose:
- create predictable covered/uncovered behavior;
- produce real Cobertura XML;
- create Git changes with known ground truth.

## Do not require

The initial environment does not require:
- company VPN;
- private repo;
- cloud;
- Docker;
- GPU;
- AI model;
- external dataset.

## Output locations

Configure test results and raw collector exports under `artifacts/test-results/`,
normalized Cobertura under `artifacts/tc1/coverage.cobertura.xml`, and ReportGenerator
HTML under `artifacts/tc1/coverage/`. Paths are relative to the repository root.
See [Generated output policy](03_ARCHITECTURE.md#generated-output-policy).

## Setup verification (across WP0–WP2)

These checks are completed across WP0 (tools and sample tests), WP1 (coverage and HTML),
and WP2 (Python package and pytest). They are not all prerequisites for finishing WP0.

```text
git --version           works
python --version        works
dotnet --info           works
pytest                  can run
dotnet test             can run
coverage XML            can be produced
ReportGenerator HTML    can be produced
```

## Portability rule

Do not store absolute machine-specific paths in:
- code;
- fixtures;
- docs;
- config committed to Git.

Use repository-relative paths and CLI arguments.
