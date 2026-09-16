"""Map reliable aggregate branch evidence at changed Git head lines.

Cobertura condition data is collector aggregate evidence, not source-level true/false
identity. This mapper preserves that aggregate and returns unknown whenever it cannot
be established safely.
"""

import re

from tc1.models import BranchAggregate, BranchResult, CoverageReport, GitDiffResult, SourceLocation
from tc1.path_normalizer import PathMatch, PathMatchStatus, match_coverage_paths

_CONDITION_COVERAGE = re.compile(r"[0-9]+(?:\.[0-9]+)?% \(([0-9]+)/([0-9]+)\)")


def _unknown(location: SourceLocation, reason: str) -> BranchResult:
    return BranchResult(location, reason)


def _has_branch_signal(entry) -> bool:
    return entry.branch is not None or entry.condition_coverage is not None or bool(entry.conditions)


def _aggregate(entry) -> BranchAggregate | None:
    """Read collector counts without assigning semantic branch identities."""
    if entry.branch is None or entry.branch.casefold() != "true" or entry.condition_coverage is None:
        return None
    match = _CONDITION_COVERAGE.fullmatch(entry.condition_coverage)
    if match is None:
        return None
    covered, total = (int(value) for value in match.groups())
    if total == 0 or covered > total:
        return None
    return BranchAggregate(covered, total)


def _branch_result(location: SourceLocation, match: PathMatch, unavailable_reason: str | None) -> BranchResult | None:
    if match.status is not PathMatchStatus.MATCHED or len(match.classes) != 1:
        # Without a unique class line record we cannot even identify a branch candidate.
        return None
    coverage_class = match.classes[0]
    if not coverage_class.lines_present:
        return None
    entries = tuple(item for item in coverage_class.lines if item.location.line == location.line)
    signals = tuple(item for item in entries if _has_branch_signal(item))
    if not signals:
        return None
    if len(entries) != 1:
        return _unknown(location, "ambiguous_branch_line_evidence")
    entry = entries[0]
    if entry.branch is not None and entry.branch.casefold() == "false":
        if entry.condition_coverage is None and not entry.conditions:
            return None
        if unavailable_reason is not None:
            return _unknown(location, f"file_unavailable:{unavailable_reason}")
        return _unknown(location, "branch_metadata_contradictory")
    if unavailable_reason is not None:
        return _unknown(location, f"file_unavailable:{unavailable_reason}")
    aggregate = _aggregate(entry)
    if aggregate is None:
        return _unknown(location, "branch_aggregate_unreliable")
    return BranchResult(location, "aggregate_condition_coverage", aggregate)


def map_changed_branches(changes: GitDiffResult, coverage: CoverageReport) -> tuple[BranchResult, ...]:
    """Map reliable branch aggregates at changed lines in Git file/hunk/line order."""
    matches = match_coverage_paths(coverage, (item.path for item in changes.files), changes.repo_root)
    results = []
    for file_change, match in zip(changes.files, matches, strict=True):
        for line_number in file_change.changed_lines:
            result = _branch_result(SourceLocation(file_change.path, line_number), match, file_change.unavailable_reason)
            if result is not None:
                results.append(result)
    return tuple(results)