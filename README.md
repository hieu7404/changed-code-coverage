# TC1 — Changed-Code Coverage Analyzer

TC1 checks which lines changed between two Git revisions were exercised by tests.
It combines a committed Git diff with Cobertura coverage and produces JSON,
Markdown and HTML reports for reviewing C#/.NET changes.

**The local end-to-end flow is implemented and usable for coverage review.**
TC1 is report-only: it has no CI workflow, coverage threshold or blocking CI gate.
A trustworthy threshold policy still needs representative diff validation and a
team decision about unknown evidence, exclusions and minimum usable evidence.

```text
Tests at head -> Cobertura XML + ReportGenerator HTML
Git base...head + Cobertura -> TC1 -> JSON / Markdown / HTML
```

## Start using TC1

Requirements: Python 3.11+ and Git. Producing fresh sample coverage also requires
the .NET SDK selected by [sample-dotnet/global.json](sample-dotnet/global.json)
and PowerShell for its collection script.

From the repository root, on Linux/macOS:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python -m tc1 analyze --help
```

On Windows PowerShell, use `python -m venv .venv`, then
`.venv/Scripts/python.exe -m pip install -e ".[dev]"`. Use that Python executable
in place of `python` below if the environment is not activated.

With coverage collected from the selected committed head, replace `BASE_REV`:

```bash
python -m tc1 analyze --repo . --base BASE_REV --head HEAD --coverage artifacts/tc1/coverage.cobertura.xml --json artifacts/tc1/report.json --markdown artifacts/tc1/report.md --html artifacts/tc1/index.html
```

Open `artifacts/tc1/index.html`. For collection, a sample diff, ReportGenerator,
another local C# repository and the optional viewer, follow the
[end-to-end runbook](docs/01_DEMO_RUNBOOK.md).

## Read the result

| Finding | Meaning |
| --- | --- |
| `covered` | One reliable explicit line entry has positive hits |
| `uncovered` | One reliable explicit line entry has zero hits |
| `unknown` | Evidence is missing, ambiguous or unreliable |
| Excluded | An explicit caller-supplied path rule removes the line from analysis |

Changed-code coverage (classifiable coverage) is `covered / (covered + uncovered)`.
Reports show it beside the line `classifiable rate`: `(covered + uncovered) /
in-scope changed lines`, and `unknown rate`: `unknown / in-scope changed lines`.
Unknown and excluded findings stay visible outside the coverage denominator; an
empty denominator is `null`, not 0%.
Branches use reliable collector aggregates without guessed true/false identities.
Coverage demonstrates execution; it does not establish assertion quality or code correctness.

## Documentation

- [Documentation map](docs/00_START_HERE.md)
- [Current status and remaining work](docs/03_TASK_CHECKLIST.md)
- [Coverage rules and architecture](docs/02_ARCHITECTURE.md)
- [Validation evidence and real-pilot procedure](docs/04_EVALUATION_PLAN.md)

The controlled evaluation covers 14 reviewed scenarios. Representative real-diff
validation and reviewer-time research remain pending; see the validation document
for the limits of these results.

This is a standalone repository. Runtime analysis uses Python's standard library
and the Git CLI; it requires no company workspace, AI service or database.
Generated output belongs under ignored `artifacts/`. Contributors follow [AGENTS.md](AGENTS.md).
