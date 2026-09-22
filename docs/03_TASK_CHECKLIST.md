# Current status

The local end-to-end product is usable for reviewing changed-code coverage.
This checklist tracks capabilities and remaining validation, rather than historical
implementation stages.

## Available

- [x] Controlled C#/.NET sample with xUnit, Coverlet and ReportGenerator collection.
- [x] Committed Git comparison using a unique merge base and changed head lines.
- [x] Cobertura parsing, portable lexical paths and ambiguity detection.
- [x] Covered / uncovered / unknown line findings with explicit reasons.
- [x] Reliable aggregate branch findings without semantic true/false guesses.
- [x] Explicit path exclusions and shared metrics with visible coverage and line-evidence denominators.
- [x] JSON, Markdown and standalone HTML reports; optional ReportGenerator link.
- [x] Static local viewer for an existing JSON report.
- [x] Automated module/integration tests and 14 reviewed controlled evaluation cases.
- [x] End-to-end runbook and real-pilot observation template.
- [x] Preliminary public C# repository test/collector compatibility run.

## Still to validate

- [ ] Representative real committed diffs with classifiable findings and recorded manual review.
- [ ] Unknown rates and discrepancy causes across those diffs.
- [ ] Reviewer-time benefit, using the separate voluntary human-review protocol.

The preliminary compatibility run does not complete real-diff validation.
See [validation evidence](04_EVALUATION_PLAN.md) for what each result establishes.

## CI status

- [ ] Optional report-only CI workflow, after sampled mappings are manually validated.
- [ ] A trustworthy, explicitly approved threshold policy, if a gate is later requested.
- [ ] Optional blocking gate, only after that validation and policy exist.

There is currently **no CI workflow or blocking coverage gate**. A successful
`tc1 analyze` exits 0 even when findings are uncovered or unknown. It does not
certify that a change is safe to merge. No default threshold is proposed.

## Next bounded step

Run TC1 on a small reviewed set of committed C# diffs, record classifiable findings,
unknowns and mapping discrepancies using the [pilot procedure](04_EVALUATION_PLAN.md#real-pilot-validation).
Use that evidence to decide whether report-only CI is useful before defining any gate.
