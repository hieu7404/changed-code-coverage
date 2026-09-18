"""Validate explicit, portable path exclusion rules."""

from pathlib import Path

import pytest

from tc1.errors import InputError
from tc1.exclusions import partition_excluded_changes
from tc1.models import ChangeKind, DiffHunk, FileChange, GitDiffResult


def _change(path: str, *lines: int) -> FileChange:
    return FileChange(
        path, ChangeKind.MODIFIED, "100644", "100644",
        (DiffHunk(1, 1, min(lines), len(lines), tuple(lines), (1,)),),
    )


def _changes(*files: FileChange) -> GitDiffResult:
    return GitDiffResult(Path("repo"), "base", "head", "merge", files)


def test_partition_preserves_included_files_and_excluded_git_line_order():
    included, excluded = partition_excluded_changes(
        _changes(
            _change("src/Service.cs", 4),
            _change("src/Generated/One.g.cs", 8, 10),
            _change("src/Generated/Two.cs", 12),
        ),
        ("**/*.g.cs", "src/Generated/**"),
    )

    assert [item.path for item in included.files] == ["src/Service.cs"]
    assert [(item.location.path, item.location.line, item.reason) for item in excluded] == [
        ("src/Generated/One.g.cs", 8, "path_rule:**/*.g.cs"),
        ("src/Generated/One.g.cs", 10, "path_rule:**/*.g.cs"),
        ("src/Generated/Two.cs", 12, "path_rule:src/Generated/**"),
    ]


def test_globstar_matches_root_and_nested_paths_but_star_does_not_cross_slashes():
    changes = _changes(
        _change("Root.g.cs", 1),
        _change("nested/Child.g.cs", 2),
        _change("nested/deep/Other.cs", 3),
    )

    included, excluded = partition_excluded_changes(changes, ("**/*.g.cs", "nested/*.cs"))

    assert [item.path for item in included.files] == ["nested/deep/Other.cs"]
    assert [item.location.path for item in excluded] == ["Root.g.cs", "nested/Child.g.cs"]


def test_patterns_are_portable_and_matching_is_case_sensitive():
    included, excluded = partition_excluded_changes(
        _changes(_change("src/Generated/File.cs", 5), _change("SRC/Generated/Other.cs", 6)),
        (r".\src\Generated\**",),
    )

    assert [item.path for item in included.files] == ["SRC/Generated/Other.cs"]
    assert excluded[0].reason == "path_rule:src/Generated/**"


@pytest.mark.parametrize("pattern", ["", "   ", "/absolute/**", "C:/repo/**", "../outside/**"])
def test_invalid_patterns_are_rejected(pattern):
    with pytest.raises(InputError, match="exclude-path"):
        partition_excluded_changes(_changes(_change("src/A.cs", 1)), (pattern,))
