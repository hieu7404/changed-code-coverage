# Decision log

This is a concise record of accepted choices. IDs are retained from the original
implementation log; detailed historical execution notes remain in Git history.
Current behavior is defined in [architecture and coverage rules](02_ARCHITECTURE.md).

## Foundation

| ID | Accepted decision |
| --- | --- |
| D001 | Keep the repository standalone and portable, without private workspace dependencies. |
| D002 | Validate first with a controlled local C# sample. |
| D003 | Use one existing C# project for a real pilot before widening language support. |
| D004 | Reuse each pilot's existing test framework. |
| D005 | Use Cobertura XML as the initial interchange format. |
| D006 | Implement deterministic mapping and reporting in Python. |
| D007 | Preserve covered, uncovered and unknown as distinct results. |
| D008 | Report branches only from reliable collector evidence. |
| D009 | Use ReportGenerator as supporting coverage visualization. |
| D010 | Start any CI integration with reports; a gate requires validation and explicit threshold approval. |
| D011 | Put generated evidence under ignored `artifacts/`; commit only reviewed fixtures and durable docs. |

## Implementation contracts

| ID | Accepted decision |
| --- | --- |
| D012 | The sample targets net10.0, pins SDK 10.0.401 with latest-patch roll-forward, and uses xUnit/VSTest. |
| D013 | Use a synthetic discount policy with an intentionally untested bulk path. Its current values live in the sample source; the original 20% bulk discount was later changed to 25%. |
| D014 | Sample collection uses Coverlet 6.0.4 and ReportGenerator 5.5.11. Select the current TRX attachment, preserve XML bytes, and record source/XML hashes. |
| D015 | Use a Python 3.11+ setuptools package, standard-library runtime, argparse CLI and pytest development extra. Both CLI entry points share one implementation. |
| D016 | Compare a unique merge base to committed head. Disable rename/copy inference; preserve unsupported-file limitations without fabricated candidates. |
| D017 | Preserve class-level evidence, method records and raw metadata separately. Reject malformed required fields; never synthesize missing hits. |
| D018 | Resolve paths lexically without basename guessing. The original one-class-per-file restriction is superseded by D026. |
| D019 | Classify a changed line only from unique explicit primary evidence. Missing or repeated evidence stays unknown; D026 defines the cross-class rule. |
| D020 | Report branch aggregates from collector counts without inferred semantic true/false identities. |
| D021 | Attach one shared metric summary to `AnalysisResult`; exclude unknown/excluded from percentages and use null for an empty denominator. |
| D022 | Write only explicitly requested, distinct report destinations. Link a caller-supplied ReportGenerator page and expose its availability. |
| D023 | Evaluate the production pipeline against reviewed manifests and expected public findings. Keep reviewer-time research separate. |
| D024 | Require an authorized local C# pilot, committed diffs, suitable coverage and manual observations before claiming real-pilot validation. |
| D025 | The user-approved static viewer displays existing JSON without backend, persistence or independent coverage calculations. |

## D026 — Multiple classes per source file

Several Cobertura classes, including generated async/iterator classes, may name the
same source file. This is usable when every class identifies that one Git path.
Exactly one explicit entry across those classes must identify a changed line.
Repeated same-line evidence remains unknown even when hit counts agree. A class
that can identify multiple changed paths remains ambiguous. No compiler-name
heuristic selects a preferred class.

## D027 — Explicit path exclusions

Repeatable `--exclude-path` arguments use portable repository-relative globs.
First match wins before line/branch mapping. Every excluded head line retains its
rule and stays outside the denominator; no excluded branch outcome count is invented.
There are no defaults or project configuration files.

## D028 — Current-product documentation and report-only boundary

Consolidate documentation around the working end-to-end product instead of work-package
diaries. Number the seven documents in `docs/` from `00` to `06` in reading order,
update local READMEs and contributor references, and remove obsolete
bootstrap prompts and the unrelated project brainstorm from the active tree.
Historical content remains in Git history.

The local analyzer is usable for coverage review. No CI workflow or coverage gate is
implemented. A trustworthy threshold has not been established; representative mapping
validation, unknown/exclusion policy and explicit team approval must precede a gate.
Report-only CI is a separate optional follow-up, not a completed feature.

## D029 — Separate line-evidence sufficiency from coverage

Changed-code coverage remains `covered / (covered + uncovered)`. Reports also
publish line-only classifiable and unknown rates, `classifiable / in_scope` and
`unknown / in_scope`, where in-scope means changed-line candidates after explicit
exclusions. This prevents a high coverage percentage from being read as evidence
for all changed lines. Branches do not receive analogous rates because their
candidates mix known outcomes with unknown locations and are not a source-branch
inventory.

## D030 — Verify coverage provenance at whole-run scope

An optional versioned JSON sidecar records collection commit, dirty state,
collector/version, command, target framework, coverage XML SHA-256 and timestamp.
When it is supplied, TC1 verifies the selected head, clean worktree and exact XML
bytes before mapping. A mismatch fails the command rather than assigning candidate
lines `unknown`; successful reports are `verified`, while no sidecar is explicitly
`unverified`. `--require-provenance` makes verification mandatory.
