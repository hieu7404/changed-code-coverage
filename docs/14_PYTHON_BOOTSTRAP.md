# WP2 Python Bootstrap

## Status

**WP2 complete.** Validated on Windows with Python 3.14.6 and pytest 9.1.1:
43 tests passed. TC1 0.1.0 installs in a repository-local virtual environment.
Runtime code uses the standard library; pytest is a development dependency.

This establishes the Python foundation. Git diff parsing, Cobertura parsing, path
normalization, mapping, metrics and report generation remain WP3-WP9.

## Install and verify

Run from the repository root. Initial installation needs access to the Python
package index unless the dependencies are cached.

Windows PowerShell (activation is optional):

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install --cache-dir artifacts/tools/pip-cache -e ".[dev]"
.venv/Scripts/python.exe -m tc1 --help
.venv/Scripts/tc1.exe --version
.venv/Scripts/python.exe -m pytest --junitxml=artifacts/test-results/wp2/pytest.xml
.venv/Scripts/python.exe -m pip check
```

POSIX equivalent (not validated in this work package):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --cache-dir artifacts/tools/pip-cache -e ".[dev]"
.venv/bin/python -m tc1 --help
.venv/bin/tc1 --version
.venv/bin/python -m pytest --junitxml=artifacts/test-results/wp2/pytest.xml
.venv/bin/python -m pip check
```

After activating the environment, `tc1`, `python -m tc1`, and `pytest` are available
directly. Install the package before running tests; no test-only import-path override
is used. Python 3.11+ is the declared minimum; this run exercised Python 3.14.6 only.

Pytest temporary files use `artifacts/test-results/pytest-tmp/`. Pytest clears that
scratch directory on subsequent runs; keep durable run evidence outside it. JUnit
results use the explicit path above. Fixtures remain small reviewed assets under
`fixtures/`; diff/XML fixtures will be added with their parsers.

## CLI contract

Both entry points call the same `main` function.

| Command / option | WP2 behavior |
| --- | --- |
| `tc1 --help` | Show commands, exit 0 |
| `tc1 --version` | Show installed package version, exit 0 |
| `tc1 analyze --help` | Show arguments and bootstrap limitation, exit 0 |
| `--repo` | Optional; defaults to `.` |
| `--base` | Required revision argument |
| `--head` | Optional; defaults to `HEAD` |
| `--coverage` | Required Cobertura path argument |
| `--json`, `--markdown`, `--html` | Optional output path arguments; omitted values remain `None` |
| Missing/unknown arguments or command | Usage error on stderr, exit 2 |
| Syntactically valid `analyze` | Explicit not-implemented error on stderr, exit 1 |

Paths and revisions are passed to `AnalysisRequest` without checking existence,
resolving Git revisions, normalizing paths, reading coverage, or creating output.
The analysis pipeline has no implementation yet. There is no successful empty report,
coverage percentage, default threshold, or CI gate.

Example after activating the virtual environment:

```powershell
tc1 analyze --repo . --base HEAD~1 --head HEAD --coverage artifacts/tc1/coverage.cobertura.xml --json artifacts/tc1/report.json --markdown artifacts/tc1/report.md --html artifacts/tc1/index.html
```

At WP2 this intentionally exits 1 and leaves the WP1 coverage bundle intact.
Input validation and final output-path resolution will be defined as the pipeline
is implemented; this argument contract does not establish coverage provenance.

## Shared models and errors

Models are frozen dataclasses with typed tuple collections.

| Model | Responsibility |
| --- | --- |
| `AnalysisRequest` | CLI input and optional output paths |
| `SourceLocation` | Opaque source path and one-based line number |
| `LineCoverage` | Explicit nonnegative integer hits plus raw condition metadata |
| `ConditionEvidence` | Preserve collector attributes without interpreting jump identifiers |
| `CoverageStatus` | Exactly covered, uncovered, unknown |
| `LineResult` | Classification, reason, optional hits; known states require compatible hits |
| `BranchAggregate` | Reliable covered/total outcome counts; no true/false identity |
| `BranchResult` | Aggregate at a changed location, or unknown with a reason |
| `ExcludedLine` | Explicit exclusion with a reason, separate from the three states |
| `AnalysisResult` | Shared line/branch/exclusion container for future renderers |

A missing line entry is not instantiated as a zero-hit entry. Unknown line results
can retain observed hits when mapping is unreliable; hits alone do not resolve
ambiguity. An unknown branch location has `aggregate=None`; that does not assert
how many branch outcomes exist. Branch count/exclusion and summary contracts will
be refined in WP7/WP8. No denominator or percentage calculation is implemented here;
WP8 must preserve unknown/excluded visibility and use null for a zero denominator.

`TC1Error` is the expected-error base. `InputError` reserves input failures,
`ModelValidationError` rejects invalid evidence records, and
`AnalysisNotImplementedError` identifies the WP2 stub. The CLI presents expected
errors without a traceback; unexpected programming failures remain visible.

These are internal bootstrap models, not a frozen public JSON schema. Parser and
mapper work packages may extend them while retaining the evidence rules.

## Validation and limits

- 43 pytest cases cover CLI argument handling, both installed entry points, invocation
  outside the repository, expected failures, existing-output preservation, evidence
  invariants, unknown/exclusion separation, and aggregate branch records.
- JUnit evidence: `artifacts/test-results/wp2/pytest.xml`.
- `pip check` passes.
- A wheel was built under `artifacts/dist/`, installed with `--no-index --no-deps`
  in `artifacts/tools/wp2-wheel-venv/`, and both CLI entry points ran from a separate
  working directory. The analysis stub returned the expected exit code 1.
- WP2 tests do not validate mapping accuracy, denominator calculations, or report rendering.
- The C# sample and WP1 pipeline were unchanged; .NET tests were not rerun for WP2.

Next bounded step: **WP3 Git diff parser**, including revision resolution, modified/
added files, multiple files/hunks, and explicit deleted/binary/rename/copy handling.