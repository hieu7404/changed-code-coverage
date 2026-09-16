# WP11 Real-Pilot Readiness

## Status

**Readiness complete; execution pending a real local C# repository.** TC1 has no
external repository in scope, so this document does not claim collector compatibility,
mapping accuracy or review usefulness for any real project. It defines the bounded
procedure to run when an authorized local pilot is available.

Use one existing C# project and its existing test runner. Do not replace its framework,
add a CI gate, upload source/coverage, or commit generated artifacts to the pilot.

## Entry criteria

Before analyzing a pilot, record these facts in a local copy of the
[real-pilot manifest template](../eval/real_pilot_manifest.template.json):

- an authorized local working-tree repository, with `base` and `head` commits and a
  unique merge base available locally;
- a small, reviewable committed diff at `head`; uncommitted/staged files are outside
  the TC1 comparison contract;
- the existing tests pass at `head`;
- a collector produces valid class-level Cobertura XML at `head`;
- the intended source paths can be sampled against the Cobertura class filenames and
  source roots;
- a named owner/reviewer can manually check a small sample of findings.

A private/offline repository is valid. Do not put its absolute path, source content,
credentials or internal URLs in this repository. Generated evidence belongs in the
pilot's ignored `artifacts/` area or another approved local location.

## Collector selection

1. Reuse the pilot's existing test framework and coverage mechanism if it can emit
   Cobertura XML with class-level line hits.
2. If it cannot, try Coverlet only when compatible with that runner/project; it is
   validated for the local sample, not automatically for every C# project.
3. Before relying on branch output, inspect one export line with `branch="true"` and
   a valid `condition-coverage="<percent>% (<covered>/<total>)"` value. Otherwise
   branch findings may legitimately be absent or `unknown`.
4. Keep the original collector export immutable. Normalize/copy only the selected
   Cobertura file used by TC1.

A malformed export, missing class-level evidence or path mismatch is an evaluation
observation, not a reason to label changed code uncovered.

## Pilot run

Run from the TC1 checkout after the package is installed. Substitute only local,
authorized values; use absolute paths to avoid resolving coverage/output against the
wrong working directory.

```powershell
$targetRepo = '<authorized-local-repository>'
$base = '<reviewed-base-commit-or-ref>'
$head = '<reviewed-head-commit-or-ref>'
$coverage = '<target-artifacts>/tc1/coverage.cobertura.xml'
$output = '<target-artifacts>/tc1'
$reportGenerator = '<target-artifacts>/tc1/coverage/index.html'

.venv/Scripts/tc1.exe analyze `
  --repo $targetRepo `
  --base $base `
  --head $head `
  --coverage $coverage `
  --json "$output/report.json" `
  --markdown "$output/report.md" `
  --html "$output/index.html" `
  --report-generator-html $reportGenerator
```

If Git reports dubious ownership, only for a repository you trust, add that exact
path as a Git safe directory using the repository owner's approved workflow. Do not
make a broad safe-directory exception.

## Manual validation sample

For each selected diff, compare Git patch, Cobertura XML/ReportGenerator and TC1 JSON.
Record the result locally using the manifest template:

| Check | Expected observation |
| --- | --- |
| Changed-line inventory | Every added head line appears once, in Git order |
| Positive explicit hit | `covered` with the observed hit count |
| Explicit zero hit | `uncovered` with hit count zero |
| Missing/ambiguous evidence | `unknown`, never silently `uncovered` |
| Reliable branch aggregate | Collector covered/total count preserved without true/false labels |
| Report consistency | JSON, Markdown and HTML show the same stored summaries/findings |
| Supporting evidence | ReportGenerator link is available or visibly marked unavailable |

Classify each checked finding as `match`, `mapping discrepancy`, `coverage provenance
issue`, or `collector/path limitation`. Do not change mapper semantics based on a
single unreviewed observation.

## Acceptance and follow-up

The real-pilot execution is ready to record as complete only after:

- the selected collector/profile is documented;
- a sampled set of real committed diffs has manual observations;
- any unknown rate and discrepancy causes are visible;
- artifacts remain report-only; no coverage threshold or CI gate is introduced.

Use the findings to decide whether WP12 report-only CI is appropriate. A reviewer-time
pilot may run on the same diff set, following the WP10 protocol, but is not required
for this readiness work.