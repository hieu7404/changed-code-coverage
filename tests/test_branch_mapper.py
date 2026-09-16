"""WP7 maps branch aggregates without inventing semantic branch identities."""

from pathlib import Path

from tc1.branch_mapper import map_changed_branches
from tc1.cobertura import parse_cobertura
from tc1.models import BranchAggregate, ChangeKind, DiffHunk, FileChange, GitDiffResult


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
    return map_changed_branches(changes, report)


def test_changed_branch_line_exposes_aggregate_without_true_false_identity():
    results = mapped(coverage(
        '<class filename="src/A.cs"><lines>'
        '<line number="8" hits="3" branch="True" condition-coverage="50% (1/2)"/>'
        '</lines></class>'
    ), change("src/A.cs", 8))
    assert len(results) == 1
    assert results[0].location.path == "src/A.cs"
    assert results[0].location.line == 8
    assert results[0].reason == "aggregate_condition_coverage"
    assert results[0].aggregate == BranchAggregate(1, 2)


def test_zero_covered_outcomes_and_decimal_percentages_are_valid_aggregates():
    results = mapped(coverage(
        '<class filename="src/A.cs"><lines>'
        '<line number="3" hits="0" branch="true" condition-coverage="0.0% (0/3)"/>'
        '</lines></class>'
    ), change("src/A.cs", 3))
    assert results[0].aggregate == BranchAggregate(0, 3)


def test_non_branch_changed_lines_do_not_become_branch_candidates():
    results = mapped(coverage(
        '<class filename="src/A.cs"><lines><line number="3" hits="4" branch="False"/></lines></class>'
    ), change("src/A.cs", 3, unavailable_reason="binary_file"))
    assert results == ()


def test_branch_signals_without_reliable_aggregate_become_unknown():
    missing = mapped(coverage(
        '<class filename="src/A.cs"><lines><line number="3" hits="4" branch="true"/></lines></class>'
    ), change("src/A.cs", 3))
    malformed = mapped(coverage(
        '<class filename="src/A.cs"><lines><line number="4" hits="4" branch="true" condition-coverage="not measured"/></lines></class>'
    ), change("src/A.cs", 4))
    contradictory = mapped(coverage(
        '<class filename="src/A.cs"><lines><line number="5" hits="4" branch="False" condition-coverage="50% (1/2)"/></lines></class>'
    ), change("src/A.cs", 5))
    assert [item.reason for item in missing + malformed] == ["branch_aggregate_unreliable", "branch_aggregate_unreliable"]
    assert all(item.aggregate is None for item in missing + malformed)
    assert contradictory[0].reason == "branch_metadata_contradictory"


def test_duplicate_branch_line_evidence_is_unknown_even_when_equal():
    results = mapped(coverage(
        '<class filename="src/A.cs"><lines>'
        '<line number="3" hits="4" branch="true" condition-coverage="50% (1/2)"/>'
        '<line number="3" hits="4" branch="true" condition-coverage="50% (1/2)"/>'
        '</lines></class>'
    ), change("src/A.cs", 3))
    assert results[0].reason == "ambiguous_branch_line_evidence"
    assert results[0].aggregate is None


def test_method_only_and_unmatched_path_evidence_do_not_invent_branch_candidates():
    method_only = mapped(coverage(
        '<class filename="src/A.cs"><methods><method><lines>'
        '<line number="3" hits="4" branch="true" condition-coverage="50% (1/2)"/>'
        '</lines></method></methods></class>'
    ), change("src/A.cs", 3))
    unmatched = mapped(coverage(
        '<class filename="src/A.cs"><lines><line number="3" hits="4" branch="true" condition-coverage="50% (1/2)"/></lines></class>'
    ), change("src/B.cs", 3))
    assert method_only == ()
    assert unmatched == ()


def test_unavailable_file_branch_candidate_stays_unknown():
    results = mapped(coverage(
        '<class filename="src/A.cs"><lines><line number="3" hits="4" branch="true" condition-coverage="50% (1/2)"/></lines></class>'
    ), change("src/A.cs", 3, unavailable_reason="binary_file"))
    assert results[0].reason == "file_unavailable:binary_file"
    assert results[0].aggregate is None


def test_branch_results_follow_git_file_hunk_line_order():
    results = mapped(coverage(
        '<class filename="src/A.cs"><lines>'
        '<line number="8" hits="1" branch="true" condition-coverage="100% (2/2)"/>'
        '<line number="10" hits="1" branch="true" condition-coverage="50% (1/2)"/>'
        '</lines></class>'
        '<class filename="src/B.cs"><lines><line number="2" hits="1" branch="true" condition-coverage="0% (0/2)"/></lines></class>'
    ), change("src/A.cs", 8, 10), change("src/B.cs", 2))
    assert [(item.location.path, item.location.line, item.aggregate) for item in results] == [
        ("src/A.cs", 8, BranchAggregate(2, 2)),
        ("src/A.cs", 10, BranchAggregate(1, 2)),
        ("src/B.cs", 2, BranchAggregate(0, 2)),
    ]
