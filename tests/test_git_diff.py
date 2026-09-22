"""Exercise real Git revisions and paths using repositories under artifacts/."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from tc1 import git_diff
from tc1.errors import GitDiffError
from tc1.models import ChangeKind


def test_multiple_files_hunks_and_explicit_unavailable_files(git_repo):
    repo = git_repo
    original = [f"line {n}\n" for n in range(1, 13)]
    repo.write("src/Service.cs", "".join(original))
    repo.write("Removed.cs", "class Removed\n{}\n")
    repo.write("binary.dat", b"old\0binary")
    base = repo.commit()
    changed = original.copy()
    changed[1] = "changed second\ninserted third\n"
    changed[9] = "changed tenth\n"
    repo.write("src/Service.cs", "".join(changed))
    repo.write("src/Đơn hàng [1].cs", "class New\n{}\n")
    repo.write("-option.cs", "line\n")
    repo.write("Empty.cs", "")
    repo.write("binary.dat", b"new\0binary")
    (repo.path / "Removed.cs").unlink()
    head = repo.commit()

    result = git_diff.read_git_diff(repo.path / "src", base, head)
    files = {item.path: item for item in result.files}
    assert result.repo_root.resolve() == repo.path.resolve()
    assert (result.base_commit, result.head_commit, result.merge_base) == (base, head, base)
    assert list(files) == sorted(files)
    assert files["src/Service.cs"].kind is ChangeKind.MODIFIED
    assert files["src/Service.cs"].changed_lines == (2, 3, 11)
    assert len(files["src/Service.cs"].hunks) == 2
    assert files["src/Đơn hàng [1].cs"].changed_lines == (1, 2)
    assert files["-option.cs"].changed_lines == (1,)
    assert files["Empty.cs"].kind is ChangeKind.ADDED
    assert files["Empty.cs"].changed_lines == ()
    assert files["binary.dat"].is_binary is True
    assert files["binary.dat"].unavailable_reason == "binary_file"
    assert files["binary.dat"].changed_lines == ()
    assert files["Removed.cs"].kind is ChangeKind.DELETED
    assert files["Removed.cs"].unavailable_reason == "deleted_file"
    assert files["Removed.cs"].changed_lines == ()
    assert files["Removed.cs"].hunks[0].removed_lines == (1, 2)


def test_three_dot_uses_merge_base_and_ignores_worktree_and_index(git_repo):
    repo = git_repo
    repo.write("F.cs", "original\n")
    common = repo.commit()
    repo.git("checkout", "-qb", "base-side")
    repo.write("BaseOnly.cs", "base only\n")
    base = repo.commit()
    repo.git("checkout", "-qb", "head-side", common)
    repo.write("F.cs", "head change\n")
    head = repo.commit()
    repo.write("F.cs", "dirty staged content\nmore\n")
    repo.git("add", "F.cs")
    repo.write("F.cs", "dirty unstaged content\n")
    repo.write("Untracked.cs", "untracked\n")
    before = repo.git("status", "--porcelain=v1")
    result = git_diff.read_git_diff(repo.path, base, "head-side")
    assert result.merge_base == common
    assert result.base_commit == base
    assert result.head_commit == head
    assert [(item.path, item.changed_lines) for item in result.files] == [("F.cs", (1,))]
    assert repo.git("status", "--porcelain=v1") == before


def test_exact_rename_has_no_changed_head_lines(git_repo):
    repo = git_repo
    repo.write("Original.cs", "one\ntwo\n")
    base = repo.commit()
    repo.git("mv", "Original.cs", "Renamed.cs")
    head = repo.commit()
    result = git_diff.read_git_diff(repo.path, base, head)
    assert [(item.path, item.kind, item.old_path, item.changed_lines) for item in result.files] == [
        ("Renamed.cs", ChangeKind.RENAMED, "Original.cs", ()),
    ]


def test_copy_remains_an_added_file_even_when_git_config_requests_copy_detection(git_repo):
    repo = git_repo
    repo.write("Original.cs", "one\ntwo\n")
    base = repo.commit()
    repo.git("config", "diff.renames", "copies")
    repo.write("Copy.cs", "one\ntwo\n")
    repo.commit()
    result = git_diff.read_git_diff(repo.path, base)
    assert [(item.path, item.kind, item.changed_lines) for item in result.files] == [
        ("Copy.cs", ChangeKind.ADDED, (1, 2)),
    ]


def test_deletion_only_and_no_final_newline(git_repo):
    repo = git_repo
    repo.write("F.cs", "keep\nremove\n")
    repo.write("NoNewline.cs", "before")
    base = repo.commit()
    repo.write("F.cs", "keep\n")
    repo.write("NoNewline.cs", "after")
    head = repo.commit()
    files = {item.path: item for item in git_diff.read_git_diff(repo.path, base, head).files}
    assert files["F.cs"].kind is ChangeKind.MODIFIED
    assert files["F.cs"].changed_lines == ()
    assert files["F.cs"].hunks[0].removed_lines == (2,)
    assert files["NoNewline.cs"].changed_lines == (1,)


def test_git_configuration_cannot_enable_context_or_external_drivers(git_repo, monkeypatch):
    repo = git_repo
    repo.write("F.cs", "one\ntwo\nthree\n")
    repo.write(".gitattributes", "*.cs diff=tc1-test\n")
    base = repo.commit()
    repo.write("F.cs", "one\nchanged\nthree\n")
    head = repo.commit()
    repo.git("config", "diff.tc1-test.command", "tc1-command-must-not-run")
    repo.git("config", "diff.tc1-test.textconv", "tc1-command-must-not-run")
    repo.git("config", "diff.context", "100")
    repo.git("config", "diff.interHunkContext", "100")
    repo.git("config", "diff.noprefix", "true")
    repo.git("config", "diff.relative", "true")
    monkeypatch.setenv("GIT_DIFF_OPTS", "--unified=99")
    monkeypatch.setenv("GIT_DIR", "nonexistent-git-directory")
    monkeypatch.setenv("GIT_WORK_TREE", "nonexistent-worktree")
    result = git_diff.read_git_diff(repo.path, base, head)
    assert result.files[0].changed_lines == (2,)
    assert result.files[0].hunks[0].new_count == 1


def test_mode_change_and_gitlink_are_visible_without_invented_source_lines(git_repo):
    repo = git_repo
    repo.write("Mode.cs", "same\n")
    base = repo.commit()
    repo.git("update-index", "--chmod=+x", "Mode.cs")
    repo.git("update-index", "--add", "--cacheinfo", f"160000,{base},vendor/module")
    repo.git("commit", "-qm", "mode and gitlink")
    result = git_diff.read_git_diff(repo.path, base)
    files = {item.path: item for item in result.files}
    assert files["Mode.cs"].old_mode == "100644"
    assert files["Mode.cs"].new_mode == "100755"
    assert files["Mode.cs"].changed_lines == ()
    assert files["vendor/module"].unavailable_reason == "unsupported_file_type"
    assert files["vendor/module"].changed_lines == ()


def test_regular_file_to_symlink_type_change_is_explicit(git_repo):
    repo = git_repo
    repo.write("Link.cs", "regular\n")
    base = repo.commit()
    blob = repo.git("hash-object", "-w", "--stdin", input=b"target.cs")
    repo.git("update-index", "--cacheinfo", f"120000,{blob},Link.cs")
    repo.git("commit", "-qm", "type change")
    result = git_diff.read_git_diff(repo.path, base)
    assert result.files[0].kind is ChangeKind.TYPE_CHANGED
    assert result.files[0].unavailable_reason == "unsupported_file_type"
    assert result.files[0].changed_lines == ()


def test_annotated_tag_and_empty_comparison(git_repo):
    repo = git_repo
    commit = repo.commit()
    repo.git("tag", "-am", "annotated", "baseline")
    result = git_diff.read_git_diff(repo.path, "baseline")
    assert result.base_commit == result.head_commit == result.merge_base == commit
    assert result.files == ()


@pytest.mark.parametrize("revision", ["missing-revision", "--help", "", "HEAD\0bad"])
def test_invalid_revision_is_an_input_error(git_repo, revision):
    git_repo.commit()
    with pytest.raises(GitDiffError):
        git_diff.read_git_diff(git_repo.path, revision)


def test_blob_revision_is_not_accepted_as_commit(git_repo):
    repo = git_repo
    repo.write("F.cs", "content\n")
    repo.commit()
    with pytest.raises(GitDiffError):
        git_diff.read_git_diff(repo.path, "HEAD:F.cs")


@pytest.mark.parametrize("directory_exists", [False, True])
def test_invalid_repository_is_an_input_error(directory_exists):
    # pytest scratch is intentionally inside this repository's artifacts directory.
    # Use an OS-temp directory so Git cannot discover this repository as its parent.
    with tempfile.TemporaryDirectory() as temporary_directory:
        repo = Path(temporary_directory) / "not-a-repo"
        if directory_exists:
            repo.mkdir()
        with pytest.raises(GitDiffError):
            git_diff.read_git_diff(repo, "HEAD")


def test_unrelated_histories_fail(git_repo):
    repo = git_repo
    base = repo.commit()
    tree = repo.git("rev-parse", "HEAD^{tree}")
    unrelated = repo.git("commit-tree", tree, input=b"unrelated\n")
    with pytest.raises(GitDiffError, match="merge-base"):
        git_diff.read_git_diff(repo.path, base, unrelated)


def test_multiple_merge_bases_fail_instead_of_picking_one(git_repo):
    repo = git_repo
    root = repo.commit()
    tree = repo.git("rev-parse", "HEAD^{tree}")
    a = repo.git("commit-tree", tree, "-p", root, input=b"A\n")
    b = repo.git("commit-tree", tree, "-p", root, input=b"B\n")
    first = repo.git("commit-tree", tree, "-p", a, "-p", b, input=b"first\n")
    second = repo.git("commit-tree", tree, "-p", b, "-p", a, input=b"second\n")
    with pytest.raises(GitDiffError, match="exactly one merge base"):
        git_diff.read_git_diff(repo.path, first, second)


@pytest.mark.parametrize("failure", [
    FileNotFoundError("git is missing"),
    subprocess.TimeoutExpired("git", 30),
])
def test_git_launch_failures_are_expected_errors(tmp_path, monkeypatch, failure):
    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(git_diff.subprocess, "run", fail)
    with pytest.raises(GitDiffError):
        git_diff.read_git_diff(tmp_path, "HEAD")
