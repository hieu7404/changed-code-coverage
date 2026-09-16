"""Deterministic changed-code metrics derived from mapped evidence only."""

from dataclasses import replace

from tc1.models import (
    AnalysisMetrics,
    AnalysisResult,
    CoverageStatus,
    CoverageSummary,
)


def calculate_metrics(analysis: AnalysisResult) -> AnalysisMetrics:
    """Summarize mapped line and branch evidence without reclassifying it.

    Each line finding and explicit line exclusion contributes one candidate. A
    reliable branch aggregate contributes its collector-reported number of
    outcomes; an unknown branch finding contributes one visible unknown candidate
    because its number of outcomes is intentionally not asserted.
    """

    line_covered = sum(result.status is CoverageStatus.COVERED for result in analysis.lines)
    line_uncovered = sum(result.status is CoverageStatus.UNCOVERED for result in analysis.lines)
    line_unknown = sum(result.status is CoverageStatus.UNKNOWN for result in analysis.lines)
    line_excluded = len(analysis.excluded_lines)
    line_classifiable = line_covered + line_uncovered

    branch_covered = 0
    branch_uncovered = 0
    branch_unknown = 0
    for result in analysis.branches:
        if result.aggregate is None:
            branch_unknown += 1
            continue
        branch_covered += result.aggregate.covered
        branch_uncovered += result.aggregate.total - result.aggregate.covered
    branch_classifiable = branch_covered + branch_uncovered

    return AnalysisMetrics(
        lines=CoverageSummary(
            candidates=line_classifiable + line_unknown + line_excluded,
            classifiable=line_classifiable,
            covered=line_covered,
            uncovered=line_uncovered,
            unknown=line_unknown,
            excluded=line_excluded,
        ),
        branches=CoverageSummary(
            candidates=branch_classifiable + branch_unknown,
            classifiable=branch_classifiable,
            covered=branch_covered,
            uncovered=branch_uncovered,
            unknown=branch_unknown,
            excluded=0,
        ),
    )


def attach_metrics(analysis: AnalysisResult) -> AnalysisResult:
    """Return the shared result enriched with its deterministic summaries."""

    return replace(analysis, metrics=calculate_metrics(analysis))