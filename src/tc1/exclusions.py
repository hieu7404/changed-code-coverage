"""Apply explicit repository-relative path exclusions to changed Git lines."""

from __future__ import annotations

import re
from dataclasses import replace

from tc1.errors import InputError
from tc1.models import ExcludedLine, GitDiffResult, SourceLocation


def _normalize_pattern(pattern: str) -> str:
    """Return one portable pattern or reject scope that is not repository-relative."""
    if not isinstance(pattern, str) or not pattern.strip():
        raise InputError("exclude-path patterns must be non-empty")
    normalized = pattern.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized or normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized):
        raise InputError(f"exclude-path pattern must be repository-relative: {pattern}")
    if any(part == ".." for part in normalized.split("/")):
        raise InputError(f"exclude-path pattern must not escape the repository: {pattern}")
    return normalized


def _glob_regex(pattern: str) -> re.Pattern[str]:
    """Compile the documented ``*``, ``?`` and ``**`` path-glob dialect."""
    pieces = ["^"]
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            # A globstar directory prefix may consume zero or more directories.
            pieces.append("(?:.*/)?")
            index += 3
        elif pattern.startswith("**", index):
            pieces.append(".*")
            index += 2
        elif pattern[index] == "*":
            pieces.append("[^/]*")
            index += 1
        elif pattern[index] == "?":
            pieces.append("[^/]")
            index += 1
        else:
            pieces.append(re.escape(pattern[index]))
            index += 1
    pieces.append("$")
    return re.compile("".join(pieces))


def _compiled_patterns(patterns: tuple[str, ...]) -> tuple[tuple[str, re.Pattern[str]], ...]:
    normalized = tuple(_normalize_pattern(pattern) for pattern in patterns)
    return tuple((pattern, _glob_regex(pattern)) for pattern in normalized)


def partition_excluded_changes(
    changes: GitDiffResult, patterns: tuple[str, ...],
) -> tuple[GitDiffResult, tuple[ExcludedLine, ...]]:
    """Remove explicitly excluded files from mapping and retain every changed line.

    The first matching pattern wins, preserving CLI pattern order and Git file/line
    order. Matching is case-sensitive against repository-relative Git paths.
    """
    compiled = _compiled_patterns(patterns)
    if not compiled:
        return changes, ()

    included_files = []
    excluded_lines = []
    for file_change in changes.files:
        matched_pattern = next(
            (pattern for pattern, regex in compiled if regex.fullmatch(file_change.path)),
            None,
        )
        if matched_pattern is None:
            included_files.append(file_change)
            continue
        excluded_lines.extend(
            ExcludedLine(
                SourceLocation(file_change.path, line_number),
                f"path_rule:{matched_pattern}",
            )
            for line_number in file_change.changed_lines
        )

    return replace(changes, files=tuple(included_files)), tuple(excluded_lines)
