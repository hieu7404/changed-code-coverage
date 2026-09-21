# Evaluation assets

The runner compares production mapping/metrics outputs with reviewed expectations.
After installing TC1, run from the repository root:

```bash
python eval/run_eval.py --run-id controlled
```

Use the virtual environment's Python executable if it is not activated.
Results are written to `artifacts/eval/controlled/results.json`; use another run ID
to keep multiple runs. A mismatch exits nonzero.

| Asset | Purpose |
| --- | --- |
| `cases/controlled.json` | 14 controlled Git-like change inventories |
| `expected/controlled.json` | Reviewed public findings and metrics |
| `../fixtures/evaluation/controlled.xml` | Shared Cobertura evidence |
| `run_eval.py` | Evaluation entry point |
| `real_pilot_manifest.template.json` | Template for local manual pilot observations |
| [reviewer_pilot.md](reviewer_pilot.md) | Prepared voluntary reviewer-time protocol; not yet executed |

See [validation evidence and pilot procedure](../docs/04_EVALUATION_PLAN.md) for
scenario definitions, accuracy semantics and limitations. Evaluation success does
not establish an application coverage threshold or a CI gate.
