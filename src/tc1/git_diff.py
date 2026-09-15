"""Read committed changes using merge-base..head (base...head semantics).

No checkout, index mutation, network access, external diff, or text conversion.
One raw inventory and a literal per-file patch avoid ambiguous quoted filenames.
"""

import os
import re
import subprocess
from pathlib import Path

from tc1.diff_parser import parse_file_patch, parse_raw_diff
from tc1.errors import GitDiffError
from tc1.models import ChangeKind, FileChange, GitDiffResult

_OID = re.compile(rb"(?:[0-9a-f]{40}|[0-9a-f]{64})")
_DIFF_FLAGS = (
    "--no-renames", "--no-ext-diff", "--no-textconv", "--no-color",
    "--no-relative", "--ignore-submodules=none",
)
_REGULAR_MODES = {"100644", "100755"}
# Prevent the caller's shell from redirecting --repo or overriding patch context.
_REPOSITORY_ENV = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE",
    "GIT_PREFIX", "GIT_DIFF_OPTS", "GIT_EXTERNAL_DIFF",
)


def _git(repo: Path, *args: str) -> bytes:
    env = os.environ.copy()
    for name in _REPOSITORY_ENV:
        env.pop(name, None)
    env["LC_ALL"] = "C"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    # Shallow repositories must fail on missing history rather than fetching it.
    env["GIT_NO_LAZY_FETCH"] = "1"
    try:
        result = subprocess.run(
            ["git", "--no-pager", "--literal-pathspecs", "-C", str(repo), *args],
            capture_output=True, check=False, timeout=30, env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitDiffError("Git command timed out after 30 seconds") from exc
    except (OSError, ValueError) as exc:
        raise GitDiffError(f"cannot run Git: {exc}") from exc
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitDiffError(f"Git {args[0]} failed: {detail or 'no diagnostic returned'}")
    return result.stdout


def _resolve_commit(repo: Path, revision: str) -> str:
    if not isinstance(revision, str) or not revision.strip() or "\0" in revision:
        raise GitDiffError("revision must be a non-empty string without NUL characters")
    output = _git(repo, "rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}").strip()
    if not _OID.fullmatch(output):
        raise GitDiffError("Git did not return one full commit ID")
    return output.decode("ascii")


def read_git_diff(repo: Path | str, base: str, head: str = "HEAD") -> GitDiffResult:
    """Return changed head lines, file metadata and resolved comparison revisions.

    Binary, deleted, and unsupported file kinds remain visible with explicit reasons.
    All paths are repository-relative Git names. Executability and coverage are not
    inferred here. Missing/ambiguous merge bases are errors, never an empty diff.
    """
    repository = Path(repo).resolve()
    if not repository.is_dir():
        raise GitDiffError(f"repository directory does not exist: {repository}")
    if _git(repository, "rev-parse", "--is-inside-work-tree").strip() != b"true":
        raise GitDiffError("a Git working-tree repository is required")
    root = _git(repository, "rev-parse", "--show-toplevel").removesuffix(b"\n")
    try:
        repository = Path(root.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise GitDiffError("repository root must be a UTF-8 path") from exc
    base_commit = _resolve_commit(repository, base)
    head_commit = _resolve_commit(repository, head)
    bases = _git(repository, "merge-base", "--all", base_commit, head_commit).splitlines()
    if len(bases) != 1 or not _OID.fullmatch(bases[0]):
        raise GitDiffError("comparison requires exactly one merge base; history is ambiguous or incomplete")
    merge_base = bases[0].decode("ascii")
    raw = _git(repository, "diff", *_DIFF_FLAGS, "--raw", "--no-abbrev", "-z",
               merge_base, head_commit, "--")
    files = []
    for entry in parse_raw_diff(raw):
        modes = {entry.old_mode, entry.new_mode} - {"000000"}
        if not modes <= _REGULAR_MODES:
            files.append(FileChange(
                entry.path, entry.kind, entry.old_mode, entry.new_mode,
                unavailable_reason="unsupported_file_type",
            ))
            continue
        patch = _git(
            repository, "diff", *_DIFF_FLAGS, "--patch", "--unified=0",
            "--inter-hunk-context=0", "--diff-algorithm=myers", "--no-indent-heuristic",
            "--src-prefix=a/", "--dst-prefix=b/", "--line-prefix=",
            "--output-indicator-new=+", "--output-indicator-old=-",
            "--output-indicator-context= ",
            merge_base, head_commit, "--", entry.path,
        )
        parsed = parse_file_patch(patch)
        reason = "binary_file" if parsed.is_binary else None
        if entry.kind is ChangeKind.DELETED:
            reason = "deleted_file"
        files.append(FileChange(
            entry.path, entry.kind, entry.old_mode, entry.new_mode,
            parsed.hunks, parsed.is_binary, reason,
        ))
    return GitDiffResult(repository, base_commit, head_commit, merge_base, tuple(files))
