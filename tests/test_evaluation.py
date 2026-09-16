"""Validate the committed WP10 controlled evaluation suite and runner."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tc1.errors import InputError
from tc1.evaluation import run_evaluation

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "eval" / "cases" / "controlled.json"


def test_controlled_evaluation_matches_all_reviewed_expected_results(tmp_path):
    output = tmp_path / "controlled"

    report = run_evaluation(MANIFEST, repo_root=ROOT, output_dir=output)

    assert report["passed"] is True
    assert report["summary"] == {
        "line_candidates": 16,
        "line_correct": 16,
        "line_incorrect": 0,
        "line_mapping_accuracy": 100.0,
        "branch_candidates": 3,
        "branch_correct": 3,
        "branch_incorrect": 0,
        "branch_mapping_accuracy": 100.0,
        "unknown_count": 4,
        "excluded_count": 0,
        "ambiguous_mapping_count": 1,
    }
    saved = json.loads((output / "results.json").read_text(encoding="utf-8"))
    assert saved == report
    assert len(report["cases"]) == 13


def test_evaluation_rejects_expected_case_ids_that_do_not_match_manifest(tmp_path):
    expected = tmp_path / "expected.json"
    expected.write_text('{"schema_version":"1.0","cases":{}}', encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "schema_version": "1.0",
        "coverage": str((ROOT / "fixtures" / "evaluation" / "controlled.xml")),
        "expected": expected.name,
        "cases": [{
            "id": "E01", "description": "one case",
            "files": [{"path": "src/Covered.cs", "hunks": [{"added_lines": [10]}]}],
        }],
    }), encoding="utf-8")

    with pytest.raises(InputError, match="case IDs must match"):
        run_evaluation(manifest, repo_root=ROOT)


def test_evaluation_runner_writes_artifact_and_returns_success(tmp_path):
    output = tmp_path / "runner-output"
    result = subprocess.run(
        [sys.executable, "eval/run_eval.py", "--output", str(output)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )

    assert result.returncode == 0
    assert "TC1 controlled evaluation: PASS" in result.stdout
    assert (output / "results.json").is_file()
    assert result.stderr == ""