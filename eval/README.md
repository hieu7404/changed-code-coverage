# Evaluation

WP10 commits deterministic inputs and reviewed expected results. The runner evaluates
the production mapping/metrics pipeline and writes only generated output under
`artifacts/eval/<run-id>/`.

```text
eval/
├── cases/controlled.json       # controlled Git-like change inventories
├── expected/controlled.json    # reviewed public findings and metrics
├── reviewer_pilot.md           # manual protocol; not automated or completed
├── real_pilot_manifest.template.json # private local-pilot observation template
└── run_eval.py                 # runner
```

The shared Cobertura fixture is `fixtures/evaluation/controlled.xml`. Run:

```powershell
.venv/Scripts/python.exe eval/run_eval.py --run-id controlled
```

See [WP10 evaluation](../docs/22_EVALUATION.md) for scenario definitions, accuracy
semantics, known limits and the reviewer-time pilot boundary.