"""WP5 path normalization stays lexical, portable and ambiguity-safe."""

import pytest

from tc1.cobertura import parse_cobertura
from tc1.path_normalizer import (
    PathMatchStatus, coverage_path_candidates, match_coverage_paths, normalize_git_path,
)


def report(*filenames: str, sources: tuple[str, ...] = ()):
    source_xml = "" if not sources else "<sources>" + "".join(f"<source>{item}</source>" for item in sources) + "</sources>"
    classes = "".join(f'<class filename="{item}"><lines/></class>' for item in filenames)
    return parse_cobertura(f"<coverage>{source_xml}<packages><package><classes>{classes}</classes></package></packages></coverage>".encode())


def test_normalize_git_path_uses_posix_spelling_without_case_folding():
    assert normalize_git_path(r"src\\Folder/./File.cs") == "src/Folder/File.cs"
    with pytest.raises(ValueError):
        normalize_git_path("../outside.cs")
    with pytest.raises(ValueError):
        normalize_git_path(r"C:\\repo\\File.cs")


def test_relative_source_and_filename_are_resolved_from_repo_root(tmp_path):
    candidates = coverage_path_candidates(r"nested\\File.cs", ("src/./",), tmp_path)
    assert len(candidates) == 1
    assert candidates[0].path == "src/nested/File.cs"
    assert candidates[0].source == "src/./"
    assert candidates[0].windows_syntax is True


def test_absolute_windows_path_matches_under_windows_repo_root():
    candidates = coverage_path_candidates(r"F:\\repo\\src\\File.cs", (), r"F:\\repo")
    assert candidates[0].path == "src/File.cs"
    assert candidates[0].windows_syntax is True


def test_absolute_path_outside_repo_and_drive_relative_paths_are_not_candidates(tmp_path):
    assert coverage_path_candidates("/another/File.cs", (), tmp_path) == ()
    assert coverage_path_candidates(r"C:relative\\File.cs", (), tmp_path) == ()
    assert coverage_path_candidates("File.cs", ("../outside",), tmp_path) == ()


def test_source_roots_are_not_ignored_when_filename_is_relative(tmp_path):
    paths = coverage_path_candidates("File.cs", ("src",), tmp_path)
    assert [item.path for item in paths] == ["src/File.cs"]


def test_empty_source_means_repo_root_and_absent_sources_do_too(tmp_path):
    assert coverage_path_candidates("File.cs", ("",), tmp_path)[0].path == "File.cs"
    assert coverage_path_candidates("File.cs", (), tmp_path)[0].path == "File.cs"


def test_exact_posix_path_match_is_reliable(tmp_path):
    result = match_coverage_paths(report("src/File.cs"), ["src/File.cs"], tmp_path)
    assert result[0].status is PathMatchStatus.MATCHED
    assert result[0].classes[0].filename == "src/File.cs"


def test_windows_path_case_match_is_allowed_but_preserves_git_spelling(tmp_path):
    result = match_coverage_paths(report(r"SRC\\file.cs"), ["src/File.cs"], tmp_path)
    assert result[0].status is PathMatchStatus.MATCHED
    assert result[0].git_path == "src/File.cs"


def test_posix_case_difference_is_not_silently_matched(tmp_path):
    result = match_coverage_paths(report("SRC/File.cs"), ["src/File.cs"], tmp_path)
    assert result[0].status is PathMatchStatus.UNMATCHED


def test_one_cobertura_record_that_can_name_two_changed_files_is_ambiguous(tmp_path):
    evidence = report("File.cs", sources=("first", "second"))
    results = match_coverage_paths(evidence, ["first/File.cs", "second/File.cs"], tmp_path)
    assert [item.status for item in results] == [PathMatchStatus.AMBIGUOUS, PathMatchStatus.AMBIGUOUS]
    assert all("multiple changed Git paths" in item.reason for item in results)


def test_multiple_cobertura_records_for_one_git_path_are_matched_for_line_resolution(tmp_path):
    results = match_coverage_paths(report("src/File.cs", "src/File.cs"), ["src/File.cs"], tmp_path)
    assert results[0].status is PathMatchStatus.MATCHED
    assert len(results[0].classes) == 2
    assert results[0].reason == "multiple Cobertura classes matched one Git path"


def test_case_insensitive_windows_candidate_rejects_case_colliding_git_paths(tmp_path):
    results = match_coverage_paths(report(r"SRC\\FILE.cs"), ["src/File.cs", "SRC/file.cs"], tmp_path)
    assert [item.status for item in results] == [PathMatchStatus.AMBIGUOUS, PathMatchStatus.AMBIGUOUS]


def test_duplicate_git_paths_after_normalization_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="duplicate"):
        match_coverage_paths(report("File.cs"), ["File.cs", "./File.cs"], tmp_path)
