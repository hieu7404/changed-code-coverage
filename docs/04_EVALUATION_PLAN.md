# Validation evidence and pilot procedure

TC1's local pipeline and controlled mapping suite are implemented. Controlled
correctness, compatibility with a collector, and usefulness to reviewers are
separate questions; none establishes a trustworthy CI threshold by itself.

## Reproduce automated checks

After the [Python setup](01_DEMO_RUNBOOK.md#1-install), run from the repository root:

```bash
python -m pytest
python eval/run_eval.py --run-id controlled
git diff --check
```

The evaluator writes `artifacts/eval/controlled/results.json`; choose a different
run ID to preserve another run. It uses the production parser, path resolver,
mapper and metrics, comparing complete public findings against reviewed expected
results. A mismatch returns nonzero. That exit status validates the tool's fixtures;
it is not a coverage gate for application code.

## Controlled evaluation

Inputs: [case manifest](../eval/cases/controlled.json),
[Cobertura fixture](../fixtures/evaluation/controlled.xml), and
[expected results](../eval/expected/controlled.json).

| Cases | Evidence tested |
| --- | --- |
| E01–E03 | Fully covered, partially covered and uncovered lines |
| E04 | Missing line instrumentation stays unknown |
| E05–E06 | Multiple files and hunks |
| E07–E08 | Added file and deleted-file/no-head-line behavior |
| E09 | Windows-style path normalization |
| E10–E11 | Full and partial branch aggregates |
| E12 | Missing branch aggregate stays unknown |
| E13 | Duplicate line evidence and unmatched paths stay unknown |
| E14 | Multiple classes resolve unique evidence at each changed line |

The reviewed suite has 14 passing cases: 18/18 line findings and 3/3 branch findings
correct, with 4 visible unknown findings, no exclusions and 1 ambiguous finding.
These accuracy counts compare findings per location; branch outcome denominators
remain separate in each case's coverage metrics. Missing or unexpected findings
are incorrect, and empty accuracy categories are `null`.

The suite uses controlled change inventories, not live Git acquisition. The pytest
suite separately exercises real temporary Git repositories, parsing, exclusions,
CLI behavior and report consistency. No broad real-repository accuracy or reviewer
productivity claim follows from the controlled suite's 100% result.

## Recorded C# baseline

The original Windows sample run used SDK 10.0.401, Coverlet 6.0.4 and ReportGenerator
5.5.11. Seven xUnit tests passed. Manual XML/HTML review found 10/12 instrumented
lines and 5/6 branch outcomes covered (83.33% each). These are whole-sample metrics,
not changed-code percentages or recommended thresholds.

The original source was commit `4400849`; run ID
`wp1-cf63f6c6500d4b6f878108c168eeb6ca` identifies its local ignored metadata and
manual review. Generated evidence is not shipped with a fresh checkout; reproduce
collection using the runbook. The current sample's bulk factor is `0.75m`, changed
from the original `0.80m`. The recorded baseline remains a historical observation.

At the baseline, the bulk-block brace and return (lines 14 and 16) had zero hits;
line 13 had positive hits but only 1/2 branch outcomes covered. The return at line
21 was covered. This demonstrates why line and branch results differ and why
instrumented braces cannot be discarded based on appearance.

A recorded local end-to-end check changed the untested return in commit `e8397f9`
and mapped it to uncovered with zero hits. This is a controlled sample observation,
not representative production-diff validation.

## First real-pilot result: GuardClauses

A local `ardalis/GuardClauses` pilot completed ten selected committed diffs on
2026-09-21. Each head was collected in a clean detached worktree with the project's
existing tests, Coverlet MSBuild Cobertura output and ReportGenerator. All tests
passed in every run. Reports used the explicit production-scope policy
`--exclude-path "test/**"`.

This pilot predates TC1's provenance-sidecar feature. Its clean-worktree and
collection metadata were recorded manually in local run logs, so those reports are
evidence for mapping review but not retroactively `verified` by the current CLI.

Across 2,276 changed-line candidates, 1,503 test lines were explicitly excluded.
Of the remaining 773 in-scope lines, 146 were covered, 4 uncovered and 623 unknown:
97.33% classifiable coverage (146/150), 19.40% classifiable rate (150/773), and
80.60% unknown rate (623/773). Reliable branch aggregates recorded 141/146 covered
outcomes (96.58%). The high coverage percentage is therefore not evidence for all
changed production/compatibility lines.

Twenty-one sampled observations covered covered, uncovered and unknown findings.
Twenty were mapping matches; one was a collector/path limitation; no sampled mapping
discrepancy was found. The export also exercised multiple classes for a source file,
including an async state machine. This validates the observed GuardClauses/Coverlet
combination only; it does not establish general mapping accuracy or a CI threshold.

## Second real-pilot collection: CRAP4CSharp

A second, deliberately different public repository,
`microsoft/crap4csharp`, completed a ten-committed-diff collection on 2026-09-22.
It is a single-target `net8.0` repository with separate `src/` and `tests/` paths.
Each head was collected in a clean detached worktree with its existing tests and
Coverlet collector 6.0.0 Cobertura output. All ten runs passed (1,580 tests total).
Every TC1 report used `--require-provenance` and had a verified head, clean-worktree
state and coverage XML SHA-256. The explicit scope policy was
`--exclude-path "tests/**"`.

Across 6,786 changed-line candidates, 4,200 test lines were excluded. Of 2,586
remaining in-scope lines, 692 were covered, 68 uncovered and 1,826 unknown:
91.05% classifiable coverage (692/760), 29.39% classifiable rate (760/2,586), and
70.61% unknown rate (1,826/2,586). Reliable branch aggregates recorded 253/344
covered outcomes (73.55%). Per-commit reports and the aggregate summary are retained
locally under `artifacts/eval/crap4csharp-10-diff-pilot/`.

The unknown population has two explicit causes: 1,064 `path_unmatched` lines and
762 `no_explicit_line_evidence` lines. The unmatched lines are documentation
(`docs/decisions.md`: 943, `README.md`: 72, and `docs/features/crap4csharp-port.md`:
49), which were intentionally not removed without a repository scope policy. The
remaining 762 lines are changed production code and are the appropriate population
for the planned executable-line evidence audit.

This second collection improves the classifiable rate over GuardClauses (29.39% vs
19.40%), but most in-scope lines remain unknown. It supports the conclusion that
high classifiable coverage must not be used as a gate.

A stratified manual audit then sampled 21 line findings across all ten CRAP4CSharp
diffs: five covered, five uncovered, four documentation `path_unmatched`, and seven
production `no_explicit_line_evidence` findings. All were confirmed diff-added at
the selected head. The covered and uncovered samples each had one matching Cobertura
line entry with the expected positive or zero hit count. The documentation files had
no Cobertura class, while the seven production unknowns had an instrumented source
file but no entry at the selected line. Those seven source forms were comments, a
const declaration, or control-flow labels (`case`, `else`, `try`). Two changed
branch aggregates also matched Cobertura condition coverage (`2/2` and `1/2`). The
audit recorded 23/23 matches, no mapping discrepancy, and no provenance issue in
its local ignored pilot manifest.

This supports the observed CRAP4CSharp/Coverlet mapping, but the seven-line unknown
sample is too small and structurally narrow to redefine changed-code candidates. It
therefore prompted the broader 80-line `no_explicit_line_evidence` audit below.

That broader audit completed with an 80-line stratified sample of the full
762-line `no_explicit_line_evidence` population. Selection was deterministic within
each lexical source-form group and covered all ten commits. It included every one of
the eight initially ambiguous lines. All 80 lines were diff-added, their source
filename was present in Cobertura, and none had a Cobertura entry at the selected
line. The audited sample contained 33 comments, 13 blanks, 11 declarations or
signatures, 7 braces, 4 control-flow labels, 2 using directives, and 2 attributes.
The eight ambiguous candidates were two uninitialized local declarations and six
raw-string-literal content lines; no executable statement missing explicit coverage
evidence was observed. There were no preprocessor directive findings in the full
population.

This is sufficient evidence to prototype an executable-candidate model, while
preserving the current all-changed-lines model and its denominator as the default.
It is not evidence to silently exclude a source form or alter coverage semantics.

The prototype is implemented as opt-in `--candidate-model executable_prototype`.
It acts only after TC1 maps an `unknown/no_explicit_line_evidence` finding and keeps
all explicit coverage, path issues and unrecognized source forms unchanged. On the
same ten CRAP4CSharp diffs, it moved 755/762 no-explicit findings into visible
candidate-model exclusions. Covered/uncovered counts stayed 692/68 and classifiable
coverage stayed 91.05%; in-scope lines decreased from 2,586 to 1,831, so the
classifiable rate changed from 29.39% to 41.51%. Seven multiline
signature/declaration lines remained unknown under the conservative lexer. This is a
comparison result only, not approval to change the default denominator.

## Executable-prototype cross-pilot: GuardClauses

The latest prototype was also applied to the ten historical GuardClauses diffs. The
default reanalysis reproduced its recorded 146 covered, 4 uncovered and 623 unknown
in-scope line findings; the prototype moved 461 eligible unknowns into visible model
exclusions. Covered/uncovered counts and 97.33% classifiable coverage were unchanged.
In-scope lines decreased from 773 to 312, increasing classifiable rate from 19.40%
to 48.08%. The excluded forms were 282 XML documentation comments, 49 preprocessor
directives, 34 declaration/signature lines, 31 blanks, 29 attributes, 26 braces, 9
using/namespace lines and one type declaration.

All 461 exclusions were verified against TC1's merge-base/Myers changed-line
semantics: each was a default `unknown/no_explicit_line_evidence` finding and had no
matching Cobertura line entry. A deterministic 32-line stratified source audit
covered every form, including the multi-target `#if`/`#else`/`#endif` directives
absent from the CRAP4CSharp population. The complete local record is
`artifacts/eval/guardclauses-10-diff-pilot/EXECUTABLE_PROTOTYPE_VALIDATION.md`.

The historical comparison is a regression and source-form validation, not itself a
provenance-verified coverage collection: it predates sidecars and its reports remain
`unverified`. It was not sufficient to change the default denominator, so it required
a fresh multi-target recollection before considering a collector configuration
different from Coverlet.

That G07 recollection completed on 2026-09-22. A clean worktree at
`b4771e5567fc916dd343717f4c946ffe43b7a8bb` ran 957/957 tests with Coverlet MSBuild
6.0.0 and generated a fresh Cobertura XML. Its sidecar recorded the exact commit,
clean state and SHA-256; both default and prototype reports passed
`--require-provenance` with `verified` status. The fresh XML was byte-distinct from
the historical G07 XML, yet default line/branch findings were identical, as were all
173 model exclusions. Default remained 66 covered, 2 uncovered and 252 unknown
lines (97.06% classifiable coverage; 21.25% classifiable rate); the prototype kept
66/2, reduced unknowns to 79 and raised classifiable rate to 46.26%. Branch outcomes
stayed 92/94. The retained local evidence is
`artifacts/eval/guardclauses-10-diff-pilot/G07-provenance-recollect/`.

This completes the provenance-verified multi-target recollection step. It remains
insufficient to change default semantics or establish portability beyond Coverlet;
the next model-validation step is a different collector configuration.

## Real-pilot validation

1. Choose an authorized local C# repository with its existing test runner and a
   small set of reviewable committed base/head diffs. Required history must be local.
2. Collect Cobertura from each selected head after tests pass. Record collector,
   revision and run metadata; retain the original export. Use a provenance sidecar
   with the head commit, clean-worktree state and XML SHA-256, then run TC1 with
   `--provenance ... --require-provenance`. Inspect class-level paths, line hits and
   branch aggregates before relying on them.
3. Generate reports with the [runbook](01_DEMO_RUNBOOK.md#another-local-c-repository).
4. Compare changed head lines, XML/ReportGenerator and TC1 findings. Sample covered,
   uncovered and unknown cases, exclusions when used, and reliable branch aggregates.
5. Save observations in a local copy of the
   [pilot manifest](../eval/real_pilot_manifest.template.json) under an ignored
   `artifacts/eval/<run-id>/` directory. Classify each observation as match, mapping
   discrepancy, coverage provenance issue, or collector/path limitation.

Verify line identity, hit counts, unknown reasons, explicit exclusion rules, branch
counts and agreement across all three reports. Record sampled diff/finding counts,
unknown rates and discrepancy causes. Keep private source, machine paths and internal
URLs out of committed documentation.

The two collections and their sampled mapping/evidence audits are complete, and the
prototype has been compared against both historical pilots plus a fresh,
provenance-verified multi-target GuardClauses recollection. The next validation is a
different collector configuration for the opt-in model. Report-only CI and any gate
remain later decisions; a gate still needs an approved, evidence-based threshold
policy.

## Reviewer usefulness

The [reviewer-time protocol](../eval/reviewer_pilot.md) is prepared but has not run.
It compares ordinary diff/overall-coverage review with review assisted by TC1,
recording time, correct gaps, missed gaps and incorrect conclusions. It requires
voluntary human participants; automated tests cannot substitute for those results.
