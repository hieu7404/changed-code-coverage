# Demo Runbook

## Demo goal

```text
change code
↓
run tests
↓
generate coverage
↓
run TC1
↓
inspect changed-code report
```

## Local sample demo

### 1. Create/record base revision

```bash
git rev-parse HEAD
```

### 2. Modify sample C# code

Introduce a change with:
- one path already covered;
- one path not covered.

Commit the change.

### 3. Run tests with coverage

Write raw collector output and test results under `artifacts/test-results/`.
Normalize or copy the selected export to:

```text
artifacts/tc1/coverage.cobertura.xml
```

### 4. Generate ReportGenerator HTML

Write output to:

```text
artifacts/tc1/coverage/
```

### 5. Run TC1

TC1 resolves the selected Git comparison, maps changed line and reliable aggregate
branch evidence, then writes every explicitly requested report. Pass the existing
ReportGenerator entry page explicitly so it becomes supporting evidence; TC1 neither
generates nor guesses that page. See [the WP9 report contract](21_REPORTS.md).

Target analysis invocation:

```bash
tc1 analyze \
  --repo . \
  --base <base-commit> \
  --head HEAD \
  --coverage artifacts/tc1/coverage.cobertura.xml \
  --json artifacts/tc1/report.json \
  --markdown artifacts/tc1/report.md \
  --html artifacts/tc1/index.html \
  --report-generator-html artifacts/tc1/coverage/index.html
```

The command above is the current CLI contract.

## Expected result

```text
Changed Lines
  covered
  uncovered
  unknown

Changed Branches
  covered
  uncovered
  unknown
```

## Success

A second developer should be able to reproduce:
- same Git diff;
- same coverage;
- same TC1 classifications;
- same metrics.
