# Future Work

Not MVP unless explicitly promoted.

## PR annotations
Publish changed uncovered lines/branches directly in review.

## OpenCodeReview-inspired patterns
Possible reference for:
- diff handling;
- line-level findings;
- review publishing.

Do not turn TC1 into an AI code-review system.

## Graft-inspired blast radius

```text
uncovered changed code
+
dependency graph
↓
prioritized test gaps
```

This is a separate research extension.

## AR1 connection

```text
TC1 deterministic report
+
test results
+
change list
↓
AI-generated digest
```

AI may explain evidence but must not invent coverage facts.

## UT2 → TC1 → AR1

Shared demo:

```text
UT2
historical bug → regression test
↓
TC1
show changed-code coverage
↓
AR1
explain run with linked evidence
```

Each component remains independently usable.

## More languages

Possible later:
- JavaScript/TypeScript
- Java
- Python

Each language needs validated coverage/path semantics.
