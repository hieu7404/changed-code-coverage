"""Verify denominator and unknown/exclusion handling for WP8 metrics."""

from dataclasses import FrozenInstanceError

import pytest

from tc1.errors import ModelValidationError
from tc1.metrics import attach_metrics, calculate_metrics
from tc1.models import (
    AnalysisResult,
    BranchAggregate,
    BranchResult,
    CoverageStatus,
    CoverageSummary,
    ExcludedLine,
    LineResult,
    SourceLocation,
)


def _location(line: int) -> SourceLocation:
    return SourceLocation("src/Service.cs", line)


def test_line_metrics_keep_unknown_and_excluded_visible_outside_denominator():
    analysis = AnalysisResult(
        "base", "head",
        lines=(
            LineResult(_location(1), CoverageStatus.COVERED, "positive hits", 3),
            LineResult(_location(2), CoverageStatus.UNCOVERED, "zero hits", 0),
            LineResult(_location(3), CoverageStatus.UNKNOWN, "missing evidence"),
        ),
        excluded_lines=(ExcludedLine(_location(4), "explicit exclusion"),),
    )

    summary = calculate_metrics(analysis).lines

    assert summary == CoverageSummary(4, 2, 1, 1, 1, 1)
    assert summary.coverage_percent == 50.0
    evidence = calculate_metrics(analysis).line_evidence
    assert (evidence.in_scope, evidence.classifiable, evidence.classifiable_rate, evidence.unknown_rate) == (
        3, 2, 100 * 2 / 3, 100 / 3,
    )


def test_branch_metrics_use_aggregate_outcomes_and_visible_unknown_findings():
    analysis = AnalysisResult(
        "base", "head",
        branches=(
            BranchResult(_location(1), "partial aggregate", BranchAggregate(1, 2)),
            BranchResult(_location(2), "fully covered", BranchAggregate(2, 2)),
            BranchResult(_location(3), "ambiguous collector metadata"),
        ),
    )

    summary = calculate_metrics(analysis).branches

    assert summary == CoverageSummary(5, 4, 3, 1, 1, 0)
    assert summary.coverage_percent == 75.0


def test_no_classifiable_evidence_has_null_coverage():
    analysis = AnalysisResult(
        "base", "head",
        lines=(LineResult(_location(1), CoverageStatus.UNKNOWN, "missing coverage"),),
        branches=(BranchResult(_location(1), "unreliable branch metadata"),),
        excluded_lines=(ExcludedLine(_location(2), "generated code"),),
    )

    metrics = calculate_metrics(analysis)

    assert metrics.lines == CoverageSummary(2, 0, 0, 0, 1, 1)
    assert metrics.branches == CoverageSummary(1, 0, 0, 0, 1, 0)
    assert metrics.lines.coverage_percent is None
    assert metrics.branches.coverage_percent is None
    assert metrics.line_evidence.classifiable_rate == 0.0
    assert metrics.line_evidence.unknown_rate == 100.0


def test_metrics_are_attached_to_one_immutable_analysis_result():
    analysis = AnalysisResult(
        "base", "head",
        lines=(LineResult(_location(1), CoverageStatus.COVERED, "positive hits", 1),),
    )

    enriched = attach_metrics(analysis)

    assert analysis.metrics is None
    assert enriched.metrics == calculate_metrics(analysis)
    with pytest.raises(FrozenInstanceError):
        enriched.metrics = None


@pytest.mark.parametrize("summary", [
    CoverageSummary(1, 1, 1, 0, 0, 0),
])
def test_coverage_summary_is_immutable(summary):
    with pytest.raises(FrozenInstanceError):
        summary.covered = 0


@pytest.mark.parametrize("args", [
    (1, 0, 1, 0, 0, 0),
    (1, 1, 0, 0, 1, 0),
    (1, 1, 0, 1, 0, 1),
    (True, 1, 1, 0, 0, 0),
])
def test_coverage_summary_rejects_inconsistent_counts(args):
    with pytest.raises(ModelValidationError):
        CoverageSummary(*args)
