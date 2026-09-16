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

Validated: editable installation, both CLI entry points, and 43 passing pytest cases.
See [Python bootstrap evidence and limitations](14_PYTHON_BOOTSTRAP.md).

- [x] Create Python package
- [x] Add CLI
- [x] Add pytest
- [x] Add core models
- [x] Add error types

## WP3

Validated: 104 total Python tests pass; eight reviewed patch fixtures and isolated
Git integration cases cover the comparison contract. Actual WP2 commit checked.
See [Git diff evidence and limitations](15_GIT_DIFF_PARSER.md).

- [x] Resolve base/head
- [x] Parse changed files
- [x] Parse changed lines
- [x] Handle multiple hunks
- [x] Add fixtures

## WP4

Validated: 166 total Python tests pass; five reviewed XML fixtures and the WP1
export confirm hit counts, class/method separation and branch metadata.
See [Cobertura evidence and limitations](16_COBERTURA_PARSER.md).

- [x] Parse Cobertura lines
- [x] Parse hit counts
- [x] Preserve branch metadata
- [x] Handle malformed input

## WP5
- [x] Normalize Windows paths
- [x] Normalize Linux paths
- [x] Normalize repo-relative paths
- [x] Detect ambiguity

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
