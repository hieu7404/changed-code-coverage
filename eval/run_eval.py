"""Run the committed controlled TC1 evaluation suite."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from tc1.errors import TC1Error
from tc1.evaluation import run_evaluation

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "eval" / "cases" / "controlled.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run controlled TC1 mapping evaluation.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, help="result directory; defaults under artifacts/eval")
    parser.add_argument("--run-id", help="directory name beneath artifacts/eval when --output is omitted")
    args = parser.parse_args()
    run_id = args.run_id or datetime.now(UTC).strftime("controlled-%Y%m%dT%H%M%SZ")
    output = args.output or ROOT / "artifacts" / "eval" / run_id
    try:
        report = run_evaluation(args.manifest, repo_root=ROOT, output_dir=output)
    except TC1Error as exc:
        parser.exit(1, f"tc1 evaluation: error: {exc}\n")
    summary = report["summary"]
    print(f"TC1 controlled evaluation: {'PASS' if report['passed'] else 'FAIL'}")
    print(f"Line mapping accuracy: {summary['line_mapping_accuracy']}")
    print(f"Branch mapping accuracy: {summary['branch_mapping_accuracy']}")
    print(f"Results: {output / 'results.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())