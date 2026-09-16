"""Serialize one metrics-ready analysis result as stable TC1 JSON."""

from __future__ import annotations

import json
from typing import Any

from tc1.errors import ModelValidationError
from tc1.models import AnalysisResult, BranchAggregate, CoverageSummary

SCHEMA_VERSION = "1.0"


def _require_metrics(analysis: AnalysisResult) -> None:
    if analysis.metrics is None:
        raise ModelValidationError("reports require AnalysisResult.metrics")


def _summary_data(summary: CoverageSummary) -> dict[str, int | float | None]:
    """Return stored metrics only; renderers must not recalculate percentages."""
    return {
        "candidates": summary.candidates,
        "classifiable": summary.classifiable,
        "covered": summary.covered,
        "uncovered": summary.uncovered,
        "unknown": summary.unknown,
        "excluded": summary.excluded,
        "coverage_percent": summary.coverage_percent,
    }


def _aggregate_data(aggregate: BranchAggregate | None) -> dict[str, int] | None:
    if aggregate is None:
        return None
    return {
        "covered": aggregate.covered,
        "total": aggregate.total,
        "uncovered": aggregate.total - aggregate.covered,
    }


def analysis_data(
    analysis: AnalysisResult, *, report_generator_html: str | None = None,
    report_generator_available: bool = False,
) -> dict[str, Any]:
    """Build the public JSON schema from mapped evidence and attached metrics."""
    _require_metrics(analysis)
    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "analysis": {"base": analysis.base, "head": analysis.head},
        "metrics": {
            "lines": _summary_data(analysis.metrics.lines),
            "branches": _summary_data(analysis.metrics.branches),
        },
        "lines": [
            {
                "path": item.location.path,
                "line": item.location.line,
                "status": item.status.value,
                "reason": item.reason,
                "hits": item.hits,
            }
            for item in analysis.lines
        ],
        "excluded_lines": [
            {"path": item.location.path, "line": item.location.line, "reason": item.reason}
            for item in analysis.excluded_lines
        ],
        "branches": [
            {
                "path": item.location.path,
                "line": item.location.line,
                "reason": item.reason,
                "aggregate": _aggregate_data(item.aggregate),
            }
            for item in analysis.branches
        ],
    }
    if report_generator_html is not None:
        data["supporting_evidence"] = {
            "report_generator_html": report_generator_html,
            "available": report_generator_available,
        }
    return data


def render_json(
    analysis: AnalysisResult, *, report_generator_html: str | None = None,
    report_generator_available: bool = False,
) -> str:
    """Return deterministic, UTF-8-ready JSON with a trailing newline."""
    return json.dumps(
        analysis_data(
            analysis,
            report_generator_html=report_generator_html,
            report_generator_available=report_generator_available,
        ),
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    ) + "\n"
