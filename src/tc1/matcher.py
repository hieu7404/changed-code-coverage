"""Map changed Git head lines to explicit class-level Cobertura evidence.

Only an unambiguous path match and one explicit class-level record at the changed line
can establish coverage. Multiple classes may name the same source file, but repeated
evidence at the same line remains unknown.
"""

from tc1.branch_mapper import map_changed_branches
from tc1.exclusions import partition_excluded_changes
from tc1.models import AnalysisResult, CoverageReport, CoverageStatus, GitDiffResult, LineResult, SourceLocation
from tc1.path_normalizer import PathMatch, PathMatchStatus, match_coverage_paths


def _unknown(location: SourceLocation, reason: str) -> LineResult:
    return LineResult(location, CoverageStatus.UNKNOWN, reason)


def _line_result(location: SourceLocation, match: PathMatch, unavailable_reason: str | None) -> LineResult:
    if unavailable_reason is not None:
        return _unknown(location, f"file_unavailable:{unavailable_reason}")
    if match.status is PathMatchStatus.UNMATCHED:
        return _unknown(location, "path_unmatched")
    if match.status is PathMatchStatus.AMBIGUOUS:
        return _unknown(location, "path_ambiguous")
    if not match.classes:
        return _unknown(location, "path_match_without_classes")
    classes_with_lines = tuple(item for item in match.classes if item.lines_present)
    if not classes_with_lines:
        return _unknown(location, "class_has_no_primary_line_evidence")
    entries = tuple(
        entry
        for coverage_class in classes_with_lines
        for entry in coverage_class.lines
        if entry.location.line == location.line
    )
    if not entries:
        return _unknown(location, "no_explicit_line_evidence")
    if len(entries) != 1:
        return _unknown(location, "ambiguous_line_evidence")
    entry = entries[0]
    if entry.hits > 0:
        return LineResult(location, CoverageStatus.COVERED, "explicit_positive_hits", entry.hits)
    return LineResult(location, CoverageStatus.UNCOVERED, "explicit_zero_hits", entry.hits)


def map_changed_lines(changes: GitDiffResult, coverage: CoverageReport) -> AnalysisResult:
    """Classify each changed head line from explicit, reliable evidence only.

    Results preserve Git file/hunk/line order. Deleted and binary files normally have
    no changed head lines; if unavailable file evidence has a candidate line, that
    line remains visible as unknown rather than being classified from coverage.
    """
    matches = match_coverage_paths(coverage, (item.path for item in changes.files), changes.repo_root)
    results = []
    for file_change, match in zip(changes.files, matches, strict=True):
        for line_number in file_change.changed_lines:
            location = SourceLocation(file_change.path, line_number)
            results.append(_line_result(location, match, file_change.unavailable_reason))
    return AnalysisResult(changes.base_commit, changes.head_commit, lines=tuple(results))


def map_changed_code(
    changes: GitDiffResult, coverage: CoverageReport, exclude_paths: tuple[str, ...] = (),
) -> AnalysisResult:
    """Apply explicit exclusions, then map included line and branch evidence."""
    included_changes, excluded_lines = partition_excluded_changes(changes, exclude_paths)
    lines = map_changed_lines(included_changes, coverage)
    return AnalysisResult(
        lines.base, lines.head, lines=lines.lines,
        branches=map_changed_branches(included_changes, coverage),
        excluded_lines=excluded_lines,
    )
