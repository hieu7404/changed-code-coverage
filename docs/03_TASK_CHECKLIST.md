# Current status

The local end-to-end product is usable for reviewing changed-code coverage.
This checklist tracks capabilities and remaining validation, rather than historical
implementation stages.

## Available

- [x] Controlled C#/.NET sample with xUnit, Coverlet and ReportGenerator collection.
- [x] Committed Git comparison using a unique merge base and changed head lines.
- [x] Exact-content rename handling without whole-file changed-code candidates.
- [x] Cobertura parsing, portable lexical paths and ambiguity detection.
- [x] Covered / uncovered / unknown line findings with explicit reasons.
- [x] Reliable aggregate branch findings without semantic true/false guesses.
- [x] Explicit path exclusions and shared metrics with visible coverage and line-evidence denominators.
- [x] Optional strict coverage provenance validation for commit, clean worktree and XML hash.
- [x] JSON, Markdown and standalone HTML reports; optional ReportGenerator link.
- [x] Static local viewer for an existing JSON report.
- [x] Automated module/integration tests and 14 reviewed controlled evaluation cases.
- [x] End-to-end runbook and real-pilot observation template.
- [x] Ten-diff GuardClauses/Coverlet real-pilot run with sampled manual observations.
- [x] Ten-diff CRAP4CSharp/Coverlet collection with provenance-verified reports.
- [x] Stratified CRAP4CSharp mapping audit: 21 line and 2 branch observations matched Git and Cobertura.
- [x] Stratified 80-line CRAP4CSharp `no_explicit_line_evidence` audit with no executable statement observed.
- [x] Opt-in `executable_prototype` candidate model, preserving `all_changed_lines` as default.
- [x] Historical GuardClauses cross-pilot prototype comparison: 461 eligible unknowns moved to visible model exclusions with covered/uncovered counts unchanged (historical coverage remains unverified).
- [x] Fresh GuardClauses G07 recollection with verified provenance: default/prototype findings reproduce the historical comparison despite byte-distinct XML output.

## Still to validate

- [x] Compare evidence rates and sampled mapping observations across the GuardClauses and CRAP4CSharp pilots.
- [ ] Validate the prototype against a deliberately different collector configuration before any semantic migration.
- [ ] Reviewer-time benefit, using the separate voluntary human-review protocol.

The completed pilots do not establish general mapping accuracy or a threshold.
See [validation evidence](04_EVALUATION_PLAN.md) for what each result establishes.

## CI status

- [ ] Optional report-only CI workflow, after sampled mappings are manually validated.
- [ ] A trustworthy, explicitly approved threshold policy, if a gate is later requested.
- [ ] Optional blocking gate, only after that validation and policy exist.

There is currently **no CI workflow or blocking coverage gate**. A successful
`tc1 analyze` exits 0 even when findings are uncovered or unknown. It does not
certify that a change is safe to merge. No default threshold is proposed.

## Next bounded step

Validate the opt-in executable prototype with a collector configuration other than
Coverlet. Do not change default semantics from the present evidence.
