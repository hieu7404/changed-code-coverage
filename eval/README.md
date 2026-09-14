# Evaluation

Expected future layout:

```text
eval/
├── cases/
├── expected/
└── run_eval.py
```

Controlled evaluation manifests and reviewed expected results should be committed.

All generated evaluation results and run metadata go under the repository-root
`artifacts/eval/<run-id>/`, regardless of size. Durable evaluation summaries belong in `docs/`.
See [Generated output policy](../docs/03_ARCHITECTURE.md#generated-output-policy).
