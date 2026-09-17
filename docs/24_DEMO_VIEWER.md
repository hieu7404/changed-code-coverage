# Static demo viewer

## Purpose

`demo/` is a small, dependency-free local viewer for one TC1 changed-code coverage report. It starts with a bundled sample and lets the user replace it with an existing WP9 `report.json` artifact.

The viewer adds no server, login, database, CI integration, or second coverage calculation. It displays supplied evidence only; TC1's deterministic mapper and metrics layer remain responsible for every status and percentage.

## Run locally

Serve the repository root:

```powershell
.venv/Scripts/python.exe -m http.server 8000
```

Open `http://localhost:8000/demo/`. The initial screen is a clearly marked sample that explains covered, uncovered, unknown, excluded, and branch evidence.

## Open a generated report

Generate a normal TC1 report:

```powershell
.venv/Scripts/tc1.exe analyze --repo . --base <base-revision> --head <head-revision> --coverage artifacts/tc1/coverage.cobertura.xml --json artifacts/tc1/report.json
```

Choose **Open report.json** and select that file. Alternatively, while serving the repository root, open `http://localhost:8000/demo/?report=/artifacts/tc1/report.json`.

The URL form lets the viewer resolve a relative ReportGenerator link. A locally selected file cannot reliably resolve that link, so the viewer shows its path.

## Limits

- It is a local report viewer, not a production dashboard.
- It neither runs tests nor invokes TC1; produce artifacts first.
- It does not store reports or send report content anywhere.
- Controlled evaluation remains available through `eval/run_eval.py`; it is not a separate screen in this viewer.
- It does not replace the JSON, Markdown, HTML, or ReportGenerator artifacts.
