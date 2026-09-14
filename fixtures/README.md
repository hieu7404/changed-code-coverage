# Fixtures

Small deterministic fixtures used by TC1 tests.

Expected future layout:

```text
fixtures/
├── diffs/
├── cobertura/
└── expected/
```

Fixtures should be small, readable, and committed.

All generated run output goes under the repository-root `artifacts/`, regardless of size.
Only small inputs and expected results deliberately reviewed as deterministic fixtures
belong here. See [Generated output policy](../docs/03_ARCHITECTURE.md#generated-output-policy).
