"""Run reviewed, controlled TC1 mapping evaluations without reimplementing mapping."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tc1.cobertura import read_cobertura
from tc1.errors import InputError
from tc1.matcher import map_changed_code
from tc1.metrics import attach_metrics
from tc1.models import ChangeKind, DiffHunk, FileChange, GitDiffResult
from tc1.report_json import analysis_data


@dataclass(frozen=True)
class EvaluationCase:
    """One reviewed change inventory within a controlled coverage fixture."""

    identifier: str
    description: str
    files: tuple[FileChange, ...]


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError(f"{label} {path} must contain a JSON object")
    return value


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"evaluation {field} must be a non-empty string")
    return value


def _line_numbers(value: object, field: str) -> tuple[int, ...]:
    if not isinstance(value, list) or not value:
        raise InputError(f"evaluation {field} must be a non-empty list of line numbers")
    if any(type(item) is not int or item < 1 for item in value):
        raise InputError(f"evaluation {field} must contain positive integer line numbers")
    if value != sorted(value) or len(set(value)) != len(value):
        raise InputError(f"evaluation {field} must be sorted and unique")
    return tuple(value)


def _file_change(value: object) -> FileChange:
    if not isinstance(value, dict):
        raise InputError("evaluation file entry must be an object")
    path = _require_text(value.get("path"), "file.path")
    try:
        kind = ChangeKind(value.get("kind", "modified"))
    except ValueError as exc:
        raise InputError(f"evaluation file {path!r} has an unsupported change kind") from exc
    raw_hunks = value.get("hunks", [])
    if not isinstance(raw_hunks, list):
        raise InputError(f"evaluation file {path!r} hunks must be a list")
    hunks = []
    for index, raw_hunk in enumerate(raw_hunks, start=1):
        if not isinstance(raw_hunk, dict):
            raise InputError(f"evaluation file {path!r} hunk {index} must be an object")
        added = _line_numbers(raw_hunk.get("added_lines"), f"file {path!r} hunk {index}.added_lines")
        hunks.append(DiffHunk(
            old_start=1,
            old_count=0,
            new_start=added[0],
            new_count=len(added),
            added_lines=added,
            removed_lines=(),
        ))
    modes = ("100644", "000000") if kind is ChangeKind.DELETED else ("100644", "100644")
    return FileChange(path, kind, *modes, tuple(hunks))


def _cases(document: dict[str, Any]) -> tuple[EvaluationCase, ...]:
    if document.get("schema_version") != "1.0":
        raise InputError("evaluation manifest schema_version must be '1.0'")
    raw_cases = document.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise InputError("evaluation manifest must contain a non-empty cases list")
    cases = []
    identifiers = set()
    for raw_case in raw_cases:
        if not isinstance(raw_case, dict):
            raise InputError("evaluation case must be an object")
        identifier = _require_text(raw_case.get("id"), "case.id")
        if identifier in identifiers:
            raise InputError(f"evaluation case ID is duplicated: {identifier}")
        identifiers.add(identifier)
        description = _require_text(raw_case.get("description"), f"case {identifier}.description")
        raw_files = raw_case.get("files")
        if not isinstance(raw_files, list) or not raw_files:
            raise InputError(f"evaluation case {identifier} must contain files")
        files = tuple(_file_change(item) for item in raw_files)
        if len({item.path for item in files}) != len(files):
            raise InputError(f"evaluation case {identifier} has duplicate file paths")
        cases.append(EvaluationCase(identifier, description, files))
    return tuple(cases)


def _expected(document: dict[str, Any], cases: tuple[EvaluationCase, ...]) -> dict[str, dict[str, Any]]:
    if document.get("schema_version") != "1.0":
        raise InputError("evaluation expected-result schema_version must be '1.0'")
    values = document.get("cases")
    if not isinstance(values, dict):
        raise InputError("evaluation expected results must contain a cases object")
    expected_ids = set(values)
    case_ids = {case.identifier for case in cases}
    if expected_ids != case_ids:
        raise InputError("evaluation manifest and expected-result case IDs must match")
    for identifier, result in values.items():
        if not isinstance(result, dict):
            raise InputError(f"evaluation expected result {identifier} must be an object")
    return values


def _report_data(changes: GitDiffResult, coverage) -> dict[str, Any]:
    analysis = attach_metrics(map_changed_code(changes, coverage))
    report = analysis_data(analysis)
    return {key: report[key] for key in ("metrics", "lines", "excluded_lines", "branches")}


def _finding_accuracy(expected: list[dict[str, Any]], actual: list[dict[str, Any]]) -> tuple[int, int, int]:
    """Return expected candidates, exact matches and incorrect/missing findings."""
    def key(item: dict[str, Any]) -> tuple[str, int]:
        return item["path"], item["line"]

    expected_by_key = {key(item): item for item in expected}
    actual_by_key = {key(item): item for item in actual}
    correct = sum(actual_by_key.get(location) == finding for location, finding in expected_by_key.items())
    missing_or_wrong = len(expected_by_key) - correct
    unexpected = len(set(actual_by_key) - set(expected_by_key))
    return len(expected), correct, missing_or_wrong + unexpected


def _summary(case_results: list[dict[str, Any]]) -> dict[str, int | float | None]:
    line_candidates = line_correct = line_incorrect = 0
    branch_candidates = branch_correct = branch_incorrect = 0
    unknown_count = excluded_count = ambiguous_mapping_count = 0
    for result in case_results:
        actual = result["actual"]
        expected = result["expected"]
        candidates, correct, incorrect = _finding_accuracy(expected["lines"], actual["lines"])
        line_candidates += candidates
        line_correct += correct
        line_incorrect += incorrect
        candidates, correct, incorrect = _finding_accuracy(expected["branches"], actual["branches"])
        branch_candidates += candidates
        branch_correct += correct
        branch_incorrect += incorrect
        metrics = actual["metrics"]
        unknown_count += metrics["lines"]["unknown"] + metrics["branches"]["unknown"]
        excluded_count += metrics["lines"]["excluded"] + metrics["branches"]["excluded"]
        ambiguous_mapping_count += sum(
            "ambiguous" in finding["reason"]
            for finding in (*actual["lines"], *actual["branches"])
        )

    def accuracy(correct: int, incorrect: int) -> float | None:
        denominator = correct + incorrect
        return None if denominator == 0 else 100 * correct / denominator

    return {
        "line_candidates": line_candidates,
        "line_correct": line_correct,
        "line_incorrect": line_incorrect,
        "line_mapping_accuracy": accuracy(line_correct, line_incorrect),
        "branch_candidates": branch_candidates,
        "branch_correct": branch_correct,
        "branch_incorrect": branch_incorrect,
        "branch_mapping_accuracy": accuracy(branch_correct, branch_incorrect),
        "unknown_count": unknown_count,
        "excluded_count": excluded_count,
        "ambiguous_mapping_count": ambiguous_mapping_count,
    }


def run_evaluation(
    manifest_path: Path | str,
    *,
    repo_root: Path | str,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Evaluate each manifest case through the production mapper and metrics code."""
    manifest = Path(manifest_path)
    document = _read_json(manifest, "evaluation manifest")
    coverage_name = _require_text(document.get("coverage"), "manifest.coverage")
    expected_name = _require_text(document.get("expected"), "manifest.expected")
    cases = _cases(document)
    expected = _expected(_read_json(manifest.parent / expected_name, "evaluation expected results"), cases)
    coverage = read_cobertura(manifest.parent / coverage_name)
    root = Path(repo_root).resolve()
    results = []
    for case in cases:
        changes = GitDiffResult(root, "evaluation-base", "evaluation-head", "evaluation-base", case.files)
        actual = _report_data(changes, coverage)
        reviewed = expected[case.identifier]
        results.append({
            "id": case.identifier,
            "description": case.description,
            "passed": actual == reviewed,
            "expected": reviewed,
            "actual": actual,
        })
    report = {
        "schema_version": "1.0",
        "manifest": str(manifest),
        "passed": all(result["passed"] for result in results),
        "summary": _summary(results),
        "cases": results,
    }
    if output_dir is not None:
        destination = Path(output_dir)
        try:
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "results.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
            )
        except OSError as exc:
            raise InputError(f"cannot write evaluation results to {destination}: {exc}") from exc
    return report