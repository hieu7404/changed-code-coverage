# Task Checklist

## WP0
- [x] Verify Git
- [x] Verify Python
- [x] Verify .NET
- [x] Create repo layout
- [x] Create local C# sample
- [x] Add sample tests
- [x] Run `dotnet test`

## WP1

Validated: 7 tests pass; Cobertura and HTML checked against the sample.
See [coverage baseline evidence](13_COVERAGE_BASELINE.md).

- [x] Configure coverage
- [x] Produce Cobertura XML
- [x] Run ReportGenerator
- [x] Manually verify known lines/branches

## WP2
- [ ] Create Python package
- [ ] Add CLI
- [ ] Add pytest
- [ ] Add core models
- [ ] Add error types

## WP3
- [ ] Resolve base/head
- [ ] Parse changed files
- [ ] Parse changed lines
- [ ] Handle multiple hunks
- [ ] Add fixtures

## WP4
- [ ] Parse Cobertura lines
- [ ] Parse hit counts
- [ ] Preserve branch metadata
- [ ] Handle malformed input

## WP5
- [ ] Normalize Windows paths
- [ ] Normalize Linux paths
- [ ] Normalize repo-relative paths
- [ ] Detect ambiguity

## WP6
- [ ] Covered line
- [ ] Uncovered line
- [ ] Unknown line
- [ ] Reasons
- [ ] Tests

## WP7
- [ ] Branch representation
- [ ] Aggregate conditions
- [ ] Unknown on ambiguity
- [ ] Tests

## WP8
- [ ] Line denominator
- [ ] Branch denominator
- [ ] Unknown/exclusion counts
- [ ] Null coverage case

## WP9
- [ ] JSON
- [ ] Markdown
- [ ] HTML
- [ ] ReportGenerator bundle/link
- [ ] Same metrics across outputs

## WP10
- [ ] Controlled scenarios
- [ ] Expected manifests
- [ ] Eval runner
- [ ] Mapping accuracy report
- [ ] Reviewer-time pilot

## WP11
- [ ] Real pilot when available

## WP12
- [ ] Controlled fixtures pass and sampled diff mappings are manually validated
- [ ] Report-only CI

## WP13 — Optional, post-MVP
- [ ] Mapping validated and unknown rate understood
- [ ] Explicit user/team approval and threshold policy
- [ ] Optional gate only after the above conditions

## Handover
- [ ] Reproducible local setup and demo
- [ ] Evaluation summary and known limitations
- [ ] Generated outputs follow the artifact policy
