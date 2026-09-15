"""Check evidence invariants without implementing the future mapper or metrics."""

from dataclasses import FrozenInstanceError

import pytest

from tc1.errors import ModelValidationError
from tc1.models import (
    AnalysisResult, BranchAggregate, BranchResult, ConditionEvidence,
    CoverageStatus, ExcludedLine, LineCoverage, LineResult, SourceLocation,
)


@pytest.fixture
def location():
    return SourceLocation("sample/Service.cs", 13)


@pytest.mark.parametrize("line", [0, -1, True, 1.5])
def test_source_line_must_be_positive_integer(line):
    with pytest.raises(ModelValidationError):
        SourceLocation("Service.cs", line)


def test_source_path_is_preserved():
    path = r"source\nested\..\Service.cs"
    assert SourceLocation(path, 1).path == path
    with pytest.raises(ModelValidationError):
        SourceLocation(" ", 1)


@pytest.mark.parametrize("hits", [-1, True, 1.5, None])
def test_explicit_coverage_requires_nonnegative_integer_hits(location, hits):
    with pytest.raises(ModelValidationError):
        LineCoverage(location, hits)


def test_raw_condition_metadata_is_preserved(location):
    evidence = LineCoverage(
        location, 5, "50% (1/2)", (ConditionEvidence("46", "jump", "50%"),),
    )
    assert evidence.hits == 5
    assert evidence.condition_coverage == "50% (1/2)"
    assert evidence.conditions[0].number == "46"
    assert evidence.conditions[0].type == "jump"
    assert evidence.conditions[0].coverage == "50%"


@pytest.mark.parametrize(("status", "hits"), [
    (CoverageStatus.COVERED, None), (CoverageStatus.COVERED, 0),
    (CoverageStatus.UNCOVERED, None), (CoverageStatus.UNCOVERED, 2),
    (CoverageStatus.UNKNOWN, -1), ("uncovered", 0),
])
def test_line_results_reject_unsupported_classifications(location, status, hits):
    with pytest.raises(ModelValidationError):
        LineResult(location, status, "evidence", hits)


def test_unknown_and_excluded_are_preserved_separately(location):
    unknown = LineResult(location, CoverageStatus.UNKNOWN, "missing instrumentation")
    excluded = ExcludedLine(SourceLocation("sample/Generated.cs", 8), "explicit exclusion")
    result = AnalysisResult("base", "head", lines=(unknown,), excluded_lines=(excluded,))
    assert result.lines[0].status is CoverageStatus.UNKNOWN
    assert result.lines[0].hits is None
    assert result.excluded_lines == (excluded,)
    assert set(CoverageStatus) == {"covered", "uncovered", "unknown"}


def test_covered_and_uncovered_require_explicit_hits(location):
    assert LineResult(location, CoverageStatus.COVERED, "positive hits", 5).hits == 5
    assert LineResult(location, CoverageStatus.UNCOVERED, "zero hits", 0).hits == 0


@pytest.mark.parametrize(("covered", "total"), [(1, 0), (3, 2), (-1, 2), (True, 2)])
def test_invalid_branch_aggregates_are_rejected(covered, total):
    with pytest.raises(ModelValidationError):
        BranchAggregate(covered, total)


def test_branch_aggregate_and_unknown_location_are_distinct(location):
    partial = BranchResult(location, "aggregate condition coverage", BranchAggregate(1, 2))
    unknown = BranchResult(location, "ambiguous branch metadata")
    result = AnalysisResult("base", "head", branches=(partial, unknown))
    assert result.branches[0].aggregate == BranchAggregate(1, 2)
    assert result.branches[1].aggregate is None


@pytest.mark.parametrize("factory", [
    lambda loc: LineResult(loc, CoverageStatus.UNKNOWN, ""),
    lambda loc: BranchResult(loc, " "),
    lambda loc: ExcludedLine(loc, ""),
])
def test_findings_require_visible_reasons(location, factory):
    with pytest.raises(ModelValidationError):
        factory(location)


def test_records_cannot_be_reassigned(location):
    with pytest.raises(FrozenInstanceError):
        location.line = 99