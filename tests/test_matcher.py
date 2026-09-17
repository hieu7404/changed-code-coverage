"""WP6/WP7 map changed evidence without turning missing data into uncovered."""

from pathlib import Path

from tc1.cobertura import parse_cobertura
from tc1.matcher import map_changed_code, map_changed_lines
from tc1.models import BranchAggregate, ChangeKind, DiffHunk, FileChange, GitDiffResult, CoverageStatus


def coverage(classes: str):
    return parse_cobertura(
        ("<coverage><packages><package><classes>" + classes
         + "</classes></package></packages></coverage>").encode()
    )


def change(path: str, *lines: int, unavailable_reason: str | None = None) -> FileChange:
    return FileChange(
        path, ChangeKind.MODIFIED, "100644", "100644",
        (DiffHunk(1, 1, min(lines), len(lines), tuple(lines), (1,)),),
        unavailable_reason=unavailable_reason,
    )


def mapped(report, *files: FileChange):
    changes = GitDiffResult(Path("F:/repo"), "base", "head", "merge", files)
    return map_changed_lines(changes, report)


def test_explicit_hits_classify_covered_uncovered_and_missing_lines():
    result = mapped(coverage(
        '<class filename="src/Service.cs"><lines>'
        '<line number="4" hits="7"/><line number="5" hits="0"/>'
        '</lines></class>'
    ), change("src/Service.cs", 4, 5, 6))
    assert [(item.location.line, item.status, item.reason, item.hits) for item in result.lines] == [
        (4, CoverageStatus.COVERED, "explicit_positive_hits", 7),
        (5, CoverageStatus.UNCOVERED, "explicit_zero_hits", 0),
        (6, CoverageStatus.UNKNOWN, "no_explicit_line_evidence", None),
    ]
    assert (result.base, result.head) == ("base", "head")


def test_unmatched_and_ambiguous_paths_are_unknown_not_uncovered():
    unmatched = mapped(coverage('<class filename="src/A.cs"><lines/></class>'), change("src/B.cs", 3))
    ambiguous_report = parse_cobertura(
        b'<coverage><sources><source>first</source><source>second</source></sources>'
        b'<packages><package><classes><class filename="A.cs"><lines/></class>'
        b'</classes></package></packages></coverage>'
    )
    ambiguous = mapped(
        ambiguous_report,
        change("first/A.cs", 3),
        change("second/A.cs", 3),
    )
    assert unmatched.lines[0] == unmatched.lines[0].__class__(
        unmatched.lines[0].location, CoverageStatus.UNKNOWN, "path_unmatched"
    )
    assert all(item.reason == "path_ambiguous" for item in ambiguous.lines)
    assert all(item.status is CoverageStatus.UNKNOWN for item in ambiguous.lines)


def test_multiple_classes_for_one_file_resolve_unique_evidence_per_changed_line():
    result = mapped(coverage(
        '<class filename="src/A.cs" name="Primary"><lines>'
        '<line number="3" hits="2"/></lines></class>'
        '<class filename="src/A.cs" name="&lt;RunAsync&gt;d__1"><lines>'
        '<line number="4" hits="0"/></lines></class>'
    ), change("src/A.cs", 3, 4, 5))
    assert [(item.location.line, item.status, item.reason, item.hits) for item in result.lines] == [
        (3, CoverageStatus.COVERED, "explicit_positive_hits", 2),
        (4, CoverageStatus.UNCOVERED, "explicit_zero_hits", 0),
        (5, CoverageStatus.UNKNOWN, "no_explicit_line_evidence", None),
    ]


def test_same_line_in_multiple_classes_remains_ambiguous_even_with_equal_hits():
    result = mapped(coverage(
        '<class filename="src/A.cs" name="Primary"><lines>'
        '<line number="3" hits="2"/></lines></class>'
        '<class filename="src/A.cs" name="Generated"><lines>'
        '<line number="3" hits="2"/></lines></class>'
    ), change("src/A.cs", 3))
    assert result.lines[0].status is CoverageStatus.UNKNOWN
    assert result.lines[0].reason == "ambiguous_line_evidence"
    assert result.lines[0].hits is None


def test_duplicate_class_line_records_are_ambiguous_even_with_equal_hits():
    result = mapped(coverage(
        '<class filename="src/A.cs"><lines>'
        '<line number="3" hits="2"/><line number="3" hits="2"/>'
        '</lines></class>'
    ), change("src/A.cs", 3))
    assert result.lines[0].status is CoverageStatus.UNKNOWN
    assert result.lines[0].reason == "ambiguous_line_evidence"
    assert result.lines[0].hits is None


def test_method_evidence_never_falls_back_to_a_missing_primary_line_inventory():
    result = mapped(coverage(
        '<class filename="src/A.cs"><methods><method><lines>'
        '<line number="3" hits="9"/>'
        '</lines></method></methods></class>'
    ), change("src/A.cs", 3))
    assert result.lines[0].status is CoverageStatus.UNKNOWN
    assert result.lines[0].reason == "class_has_no_primary_line_evidence"


def test_unavailable_file_candidate_stays_unknown_before_coverage_is_considered():
    result = mapped(coverage(
        '<class filename="src/A.cs"><lines><line number="3" hits="9"/></lines></class>'
    ), change("src/A.cs", 3, unavailable_reason="binary_file"))
    assert result.lines[0].status is CoverageStatus.UNKNOWN
    assert result.lines[0].reason == "file_unavailable:binary_file"


def test_order_is_git_file_hunk_line_order():
    result = mapped(coverage(
        '<class filename="src/A.cs"><lines><line number="8" hits="1"/>'
        '<line number="10" hits="0"/></lines></class>'
        '<class filename="src/B.cs"><lines><line number="2" hits="3"/></lines></class>'
    ), change("src/A.cs", 8, 10), change("src/B.cs", 2))
    assert [(item.location.path, item.location.line) for item in result.lines] == [
        ("src/A.cs", 8), ("src/A.cs", 10), ("src/B.cs", 2),
    ]


def test_combined_result_keeps_line_and_branch_results_together():
    report = coverage(
        '<class filename="src/A.cs"><lines>'
        '<line number="3" hits="4" branch="true" condition-coverage="50% (1/2)"/>'
        '</lines></class>'
    )
    changes = GitDiffResult(Path("F:/repo"), "base", "head", "merge", (change("src/A.cs", 3),))
    combined = map_changed_code(changes, report)
    assert combined.lines[0].status is CoverageStatus.COVERED
    assert combined.branches[0].aggregate == BranchAggregate(1, 2)