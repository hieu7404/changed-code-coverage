# Project Brief — TC1 Coverage Report for Changed Code

## Problem

Repository-wide coverage may hide weak protection in recently changed code.

Example:

```text
Overall repository coverage: 82%
Changed-code coverage:       35%
```

A reviewer needs to know whether the **current change** is exercised by tests.

## MVP

Combine an existing coverage export with a Git diff to list:

- changed executable lines tests exercised;
- changed executable lines tests did not exercise;
- changed branches tests exercised or missed when reliable branch evidence exists;
- changed code that cannot be determined because instrumentation/mapping is missing.

Start with one C#/.NET pilot.

## Research question

> Does a changed-code report help reviewers find relevant test gaps faster than a repository-wide coverage percentage?

## Evaluate

Measure:

- mapping accuracy on controlled/sampled diffs;
- reviewer time in a small baseline comparison;
- correctness of covered/uncovered/unknown;
- explicit exclusions and denominators.

## Recommended technology

```text
Existing C# test runner
+ compatible coverage collector
+ Cobertura XML
+ ReportGenerator
+ small Python Git-diff/XML mapper
```

## MVP output

```text
artifacts/tc1/report.json
artifacts/tc1/report.md
artifacts/tc1/index.html
artifacts/tc1/coverage/
```

## Success

A reviewer should be able to move from:

```text
Overall coverage = 82%
```

to:

```text
Changed line coverage = 47%
Changed branch coverage = 50%

PaymentService.cs
  L52 uncovered
  L53 uncovered

DiscountService.cs
  branch at L41 partially covered
```

with reproducible evidence.
