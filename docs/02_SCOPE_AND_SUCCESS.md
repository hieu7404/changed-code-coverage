# Scope and Success Criteria

## In scope

- local Git repository;
- base/head revision comparison;
- one C#/.NET pilot;
- existing test runner;
- coverage collector;
- Cobertura XML normalization;
- changed-line detection;
- changed-branch reporting when reliable;
- covered/uncovered/unknown;
- explicit exclusions;
- JSON/Markdown/HTML;
- ReportGenerator coverage HTML;
- unit/integration tests;
- controlled evaluation;
- report-only CI if time permits.

## Out of scope

- LLM;
- agent orchestration;
- AI code review;
- Graft integration;
- OpenCodeReview integration;
- dependency graph;
- blast radius;
- risk ranking;
- web frontend;
- DB;
- vector DB;
- crawling;
- model download/training;
- multi-language coverage;
- blocking CI gate before validation.

## MVP Definition of Done

### Environment
- [ ] Python environment works.
- [ ] Git works.
- [ ] .NET SDK works.
- [ ] local sample tests pass.
- [ ] coverage export can be generated.

### Core
- [ ] base/head accepted.
- [ ] changed lines parsed.
- [ ] Cobertura parsed.
- [ ] paths normalized.
- [ ] line mapping works.
- [ ] branch evidence handled where reliable.
- [ ] unknown preserved.
- [ ] denominators explicit.

### Output
- [ ] JSON.
- [ ] Markdown.
- [ ] HTML.
- [ ] ReportGenerator HTML linked/bundled.

### Quality
- [ ] unit tests.
- [ ] integration test.
- [ ] deterministic fixtures.
- [ ] controlled evaluation.
- [ ] known limitations documented.

### Research
- [ ] mapping accuracy reported.
- [ ] reviewer-time pilot documented.
- [ ] no unsupported broad claims.
