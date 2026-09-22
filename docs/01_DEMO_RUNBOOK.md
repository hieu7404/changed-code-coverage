# End-to-end runbook

Run commands from the TC1 repository root unless a step says otherwise. Stop on a
failed build, test or collection; an older artifact is not evidence for a new run.

## 1. Install

Use Python 3.11+ and Git. Linux/macOS:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python -m tc1 analyze --help
```

Windows PowerShell, without activation:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m tc1 analyze --help
```

For the following `python` commands, Windows users can substitute
`.venv/Scripts/python.exe`. Initial package/tool restore needs network access or
cached packages. TC1 itself has no third-party runtime dependencies.

## 2. Choose the change

Use committed `base` and `head` revisions. TC1 compares their unique merge base to
head (`base...head`); staged, unstaged and untracked edits are not analyzed.

For a new sample experiment, record `git rev-parse HEAD` as the base, edit a sample
production line, and commit the intended change. The bulk-discount return in
`sample-dotnet/Tc1.Sample/DiscountService.cs` is deliberately untested, so a change
there is a useful uncovered-line example. See the [sample contract](../sample-dotnet/README.md).

For an existing change, select its base and head without creating a new commit.
Inspect it first:

```bash
git diff --no-renames --unified=0 BASE_REV...HEAD
```

The checkout used to build and collect coverage must match the selected head and
have no local source/test edits. TC1 does not check out revisions or verify that an
XML file came from the requested head. Keep the commit ID and run metadata together.

## 3. Run tests and collect coverage

Install the SDK selected by `sample-dotnet/global.json` (10.0.401 with latest-patch
roll-forward in the same feature band). From the repository root:

```powershell
powershell -NoProfile -File sample-dotnet/Collect-Coverage.ps1
```

With PowerShell 7, including on Linux/macOS:

```bash
pwsh -NoProfile -File sample-dotnet/Collect-Coverage.ps1
```

The recorded C# baseline was validated on Windows; the `pwsh` form is an invocation
alternative, not a claim of cross-platform collection validation. If `dotnet` is
not on PATH, pass `-Dotnet` with the installed executable's path.

The script restores, builds, runs tests, selects the current successful TRX's
Coverlet attachment and generates ReportGenerator HTML. It preserves the selected
XML byte-for-byte. Outputs:

| Path | Contents |
| --- | --- |
| `artifacts/tc1/coverage.cobertura.xml` | Cobertura input for TC1 |
| `artifacts/tc1/coverage/` | ReportGenerator HTML and summary |
| `artifacts/tc1/coverage-run.json` | Tool versions, run ID and source/XML hashes |
| `artifacts/test-results/wp1-<uuid>/` | Raw TRX, XML, logs and run metadata |

The `wp1-` directory prefix is retained by the collection script. Collections share
build/bundle destinations, so run one at a time. A failure may leave the previous
bundle in place; check the successful run metadata before using it.

## 4. Generate TC1 reports

Replace `BASE_REV` with the chosen base. This single-line command works with either
shell once the Python executable is selected:

```bash
python -m tc1 analyze --repo . --base BASE_REV --head HEAD --coverage artifacts/tc1/coverage.cobertura.xml --provenance artifacts/tc1/coverage-run.json --require-provenance --json artifacts/tc1/report.json --markdown artifacts/tc1/report.md --html artifacts/tc1/index.html --report-generator-html artifacts/tc1/coverage/index.html
```

Optional exclusions are explicit and repeatable, for example
`--exclude-path "**/*.g.cs" --exclude-path "vendor/**"`. Quote patterns so the shell
does not expand them. Exclusions remain visible with their matching rule; none are
applied by default. Choose test-source exclusions deliberately if the collector
omits test assemblies.

For an experimental comparison only, add
`--candidate-model executable_prototype`. The default is `all_changed_lines` and
does not read source text. The prototype reads UTF-8 C# from the selected Git head
only after mapping an `unknown/no_explicit_line_evidence` finding, then moves a
conservative set of audited structural forms to visible `candidate_model:...`
exclusions. It preserves explicit hits, unmatched paths and executable-looking
statements. Do not replace the default report or use this option for a gate.

## 5. Inspect and act on findings

Open `artifacts/tc1/index.html`, or read `report.md` / `report.json` in the same folder.

1. Check that coverage provenance is `verified`, then inspect the selected revisions and collection metadata.
2. Inspect uncovered changed lines against the diff and coverage evidence; add tests
   for the relevant behavior where appropriate.
3. Inspect unknown reasons before drawing conclusions. Missing instrumentation does
   not mean the line is untested.
4. Read branch counts as aggregates. A covered line can still have uncovered branch outcomes.
5. Check **Evidence available for** alongside the percentage. Changed-code coverage
   applies only to classifiable lines; classifiable rate shows what fraction of
   in-scope changed lines had direct evidence. Check unknown and excluded counts too.

After adding tests, commit the desired head, collect fresh coverage and rerun TC1
against the same intended comparison base. Coverage measures execution, not the
quality of assertions. Exit 0 means the analysis succeeded, even at 0% or `null` coverage.

## Optional static viewer

From the repository root:

```bash
python -m http.server 8000 --bind 127.0.0.1
```

Open `http://localhost:8000/demo/`. The initial dataset is a labeled presentation
sample. Choose **Open report.json**, or load the real local report through
`http://localhost:8000/demo/?report=/artifacts/tc1/report.json`.
The URL form can resolve relative ReportGenerator links; file upload shows the path.
The viewer displays stored metrics and does not run tests, invoke TC1 or persist reports.

## Another local C# repository

Reuse that project's existing test framework and compatible collector. Collect
class-level Cobertura at its selected head. From the TC1 checkout, substitute paths
relative to your current directory:

```bash
python -m tc1 analyze --repo PATH_TO_PILOT --base BASE_REV --head HEAD_REV --coverage PATH_TO_COBERTURA --provenance PATH_TO_PROVENANCE --require-provenance --json artifacts/tc1/pilot/report.json --markdown artifacts/tc1/pilot/report.md --html artifacts/tc1/pilot/index.html
```

`--coverage` and report paths resolve against the caller's working directory,
independently of `--repo`. Keep generated output in an ignored `artifacts/` area.
Follow [real-pilot validation](04_EVALUATION_PLAN.md#real-pilot-validation) before
claiming mapping accuracy for that project.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No report file | Supply at least one output option; check exit code and stderr |
| Revision or merge-base error | Required commits and a unique merge base must exist locally |
| Many `path_unmatched` findings | Cobertura filenames/source roots must identify paths inside the selected repository; no basename guessing or remapping option exists |
| Missing line or ambiguous evidence | Inspect class-level XML entries and duplicates; retain `unknown` until resolved |
| No branch percentage | Only changed lines with reliable collector branch evidence enter that denominator |
| Provenance error | Recollect coverage from a clean worktree at the selected head; the sidecar commit and XML hash must match |
| ReportGenerator unavailable | Generate HTML separately and pass the correct entry page |
| Unexpectedly empty result | Confirm the committed comparison; local edits and deletion-only changes add no head-line candidates |
