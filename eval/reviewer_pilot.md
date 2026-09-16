# Reviewer-Time Pilot Protocol

## Purpose

Test whether the TC1 changed-code report helps a reviewer identify relevant test gaps
faster than a normal diff plus overall coverage alone. This is a voluntary, manual
study protocol; it does not collect source code, credentials or personal identifiers.

## Before starting

- Choose a small reviewed set of representative C# diffs with reproducible base/head
  commits and Cobertura coverage produced at head.
- Define expected changed-code gaps independently before participant review.
- Obtain participant consent and agree how aggregate observations are stored.
- Use report-only output; do not enable a CI gate.

## Per-diff procedure

1. Present the diff and whole-project coverage summary. Record elapsed time, gaps
   identified, missed expected gaps and incorrect conclusions.
2. Present the same evidence plus TC1 JSON/Markdown/HTML findings. Record the same
   measures separately.
3. Ask for a short free-text note about `unknown`, branch aggregates and report clarity.

Counterbalance the order across participants/diffs where practical. Do not ask a
participant to assess a diff they authored if that would bias the comparison.

## Record format

Keep only aggregate/review identifiers under `artifacts/eval/<run-id>/`; move durable,
anonymized findings to `docs/`. For each observation record:

```text
diff ID
condition: baseline | TC1
elapsed seconds
gaps found
expected gaps missed
incorrect conclusions
clarity notes
```

## Interpretation

This pilot is exploratory. Small samples do not establish a general productivity claim.
Use findings to improve report wording or scenario coverage, then validate mapping
changes again with the controlled suite.