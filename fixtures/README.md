# Deterministic fixtures

Small, reviewed inputs and expected results are committed here. Generated run
output belongs under ignored `artifacts/`.

| Location | Contents |
| --- | --- |
| `diffs/` | Eight one-file patches covering hunks, additions/deletions, binary and mode-only changes |
| `cobertura/` | Five XML fixtures for sample hits, duplicates, missing evidence, namespaces and metadata |
| `expected/` | Reviewed Git parsing and Cobertura expectations |
| `evaluation/controlled.xml` | Shared evidence for the 14 controlled evaluation scenarios |

Patch fixtures retain LF through `.gitattributes`. Live Git integration tests create
isolated repositories under `artifacts/test-results/pytest-tmp/`. The sample XML
preserves original baseline line/branch evidence with portable paths and a fixed
timestamp; it is a fixture, not a fresh coverage export for the current checkout.

See [coverage rules](../docs/02_ARCHITECTURE.md) and
[validation](../docs/04_EVALUATION_PLAN.md). Scenario inventories and expected public
findings live in `eval/`.
