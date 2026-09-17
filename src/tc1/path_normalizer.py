"""Normalize Cobertura and Git paths without guessing file identity.

Git supplies repository-relative POSIX names. Cobertura supplies exporter-owned
``sources`` roots plus class filenames, which may be relative, absolute, or use
Windows separators. This module resolves them lexically against the repository
root; it never opens source files, uses basename matching, or relies on the host
operating system's path rules.

A class record is accepted only when its possible Cobertura paths identify exactly
one changed Git path. Multiple class records may identify the same source file because
C# compilers and coverage collectors can emit supporting state-machine classes for
async/iterator code. Line and branch mappers resolve those records at the changed-line
level instead of choosing an arbitrary class.
"""

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
import re
from pathlib import Path
from typing import Iterable

from tc1.models import CoverageClass, CoverageReport


class PathMatchStatus(StrEnum):
    """Whether a changed Git path has reliable Cobertura class path matches."""

    MATCHED = "matched"
    UNMATCHED = "unmatched"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class CoveragePathCandidate:
    """One repo-relative interpretation of a Cobertura class filename."""

    filename: str
    source: str | None
    path: str
    windows_syntax: bool


@dataclass(frozen=True)
class PathMatch:
    """Path-only evidence for one changed Git file; no coverage state is implied."""

    git_path: str
    status: PathMatchStatus
    classes: tuple[CoverageClass, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class _Path:
    kind: str
    anchor: str
    parts: tuple[str, ...]
    windows_syntax: bool

    @property
    def absolute(self) -> bool:
        return self.kind != "relative"


_DRIVE_ABSOLUTE = re.compile(r"^([A-Za-z]):/(.*)$", re.DOTALL)
_DRIVE_RELATIVE = re.compile(r"^[A-Za-z]:")


def _parse(raw: str) -> _Path | None:
    """Return a lexical path, or ``None`` for a path we cannot safely resolve."""
    if not isinstance(raw, str) or not raw or "\0" in raw:
        return None
    windows_syntax = "\\" in raw
    text = raw.replace("\\", "/")
    if text.startswith("//"):
        fields = text[2:].split("/")
        if len(fields) < 2 or not fields[0] or not fields[1] or fields[0] in (".", "..") or fields[1] in (".", ".."):
            return None
        kind, anchor, fields, windows_syntax = "unc", f"//{fields[0]}/{fields[1]}", fields[2:], True
    else:
        drive = _DRIVE_ABSOLUTE.match(text)
        if drive is not None:
            kind, anchor, fields, windows_syntax = "drive", drive.group(1).casefold() + ":", drive.group(2).split("/"), True
        elif _DRIVE_RELATIVE.match(text):
            return None
        elif text.startswith("/"):
            kind, anchor, fields = "posix", "/", text[1:].split("/")
        else:
            kind, anchor, fields = "relative", "", text.split("/")
    parts: list[str] = []
    for field in fields:
        if not field or field == ".":
            continue
        if field == "..":
            if not parts:
                return None
            parts.pop()
            continue
        parts.append(field)
    return _Path(kind, anchor, tuple(parts), windows_syntax)


def _repository_root(repo_root: Path | str) -> _Path:
    parsed = _parse(str(repo_root))
    if parsed is None or not parsed.absolute:
        raise ValueError("repo_root must be an absolute, non-escaping path")
    return parsed


def _same_anchor(first: _Path, second: _Path) -> bool:
    if first.kind != second.kind:
        return False
    if first.kind in ("drive", "unc"):
        return first.anchor.casefold() == second.anchor.casefold()
    return first.anchor == second.anchor


def _relative_to_root(path: _Path, root: _Path) -> tuple[str, bool] | None:
    if path.kind == "relative":
        return "/".join(path.parts), path.windows_syntax
    if not _same_anchor(path, root):
        return None
    compare_windows = path.windows_syntax or root.windows_syntax
    if compare_windows:
        root_parts = tuple(part.casefold() for part in root.parts)
        path_parts = tuple(part.casefold() for part in path.parts)
    else:
        root_parts, path_parts = root.parts, path.parts
    if path_parts[:len(root_parts)] != root_parts:
        return None
    return "/".join(path.parts[len(root.parts):]), path.windows_syntax


def normalize_git_path(path: str) -> str:
    """Normalize one Git repository-relative path without changing case."""
    parsed = _parse(path)
    if parsed is None or parsed.absolute or not parsed.parts:
        raise ValueError("Git path must be a non-empty repository-relative path")
    return "/".join(parsed.parts)


def coverage_path_candidates(filename: str, sources: Iterable[str], repo_root: Path | str) -> tuple[CoveragePathCandidate, ...]:
    """Return every safe repo-relative interpretation of Cobertura evidence."""
    root = _repository_root(repo_root)
    name = _parse(filename)
    if name is None:
        return ()
    source_values = tuple(sources)
    if name.absolute:
        bases: tuple[str | None, ...] = (None,)
    elif not source_values:
        bases = (None,)
    else:
        bases = tuple(source if source != "" else None for source in source_values)
    candidates: list[CoveragePathCandidate] = []
    seen: set[tuple[str, bool]] = set()
    for source in bases:
        if source is None:
            combined = name
        else:
            base = _parse(source)
            if base is None:
                continue
            if base.kind == "relative":
                combined = _Path(root.kind, root.anchor, root.parts + base.parts + name.parts, base.windows_syntax or name.windows_syntax)
            else:
                combined = _Path(base.kind, base.anchor, base.parts + name.parts, base.windows_syntax or name.windows_syntax)
        relative = _relative_to_root(combined, root)
        if relative is None:
            continue
        path, windows_syntax = relative
        if not path:
            continue
        key = (path.casefold() if windows_syntax else path, windows_syntax)
        if key not in seen:
            seen.add(key)
            candidates.append(CoveragePathCandidate(filename, source, path, windows_syntax))
    return tuple(candidates)


def match_coverage_paths(report: CoverageReport, git_paths: Iterable[str], repo_root: Path | str) -> tuple[PathMatch, ...]:
    """Associate every class record that maps to exactly one changed Git path."""
    _repository_root(repo_root)
    normalized_git = tuple(normalize_git_path(path) for path in git_paths)
    if len(set(normalized_git)) != len(normalized_git):
        raise ValueError("git_paths must not contain duplicate normalized paths")
    exact: dict[str, set[str]] = defaultdict(set)
    folded: dict[str, set[str]] = defaultdict(set)
    for path in normalized_git:
        exact[path].add(path)
        folded[path.casefold()].add(path)
    class_targets: dict[int, set[str]] = {}
    target_classes: dict[str, list[int]] = defaultdict(list)
    classes = report.classes
    for index, coverage_class in enumerate(classes):
        targets: set[str] = set()
        for candidate in coverage_path_candidates(coverage_class.filename, report.sources, repo_root):
            targets.update(folded[candidate.path.casefold()] if candidate.windows_syntax else exact[candidate.path])
        class_targets[index] = targets
        for target in targets:
            target_classes[target].append(index)
    matches = []
    for path in normalized_git:
        indices = target_classes[path]
        if not indices:
            matches.append(PathMatch(path, PathMatchStatus.UNMATCHED, (), "no Cobertura class path matched this Git path"))
            continue
        records = tuple(classes[index] for index in indices)
        if any(len(class_targets[index]) > 1 for index in indices):
            matches.append(PathMatch(path, PathMatchStatus.AMBIGUOUS, records, "a Cobertura class path matches multiple changed Git paths"))
        else:
            reason = (
                "one Cobertura class path matched"
                if len(indices) == 1
                else "multiple Cobertura classes matched one Git path"
            )
            matches.append(PathMatch(path, PathMatchStatus.MATCHED, records, reason))
    return tuple(matches)
