"""Pure parsers for controlled Git raw (-z) output and one-file patches.

Paths come exclusively from NUL-delimited raw metadata, never from patch headers.
The patch parser validates body counts before trusting any head-side line numbers.
"""

import re
from dataclasses import dataclass

from tc1.errors import DiffParseError
from tc1.models import ChangeKind, DiffHunk

_RAW_HEADER = re.compile(
    rb":([0-7]{6}) ([0-7]{6}) ([0-9a-f]{40}|[0-9a-f]{64}) "
    rb"([0-9a-f]{40}|[0-9a-f]{64}) ([AMDT])"
)
_HUNK = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?")
_NO_NEWLINE = "\\ No newline at end of file"
_KINDS = {"A": ChangeKind.ADDED, "M": ChangeKind.MODIFIED,
          "D": ChangeKind.DELETED, "T": ChangeKind.TYPE_CHANGED}


@dataclass(frozen=True)
class RawChange:
    path: str
    kind: ChangeKind
    old_mode: str
    new_mode: str


@dataclass(frozen=True)
class FilePatch:
    hunks: tuple[DiffHunk, ...] = ()
    is_binary: bool = False


def parse_raw_diff(data: bytes) -> tuple[RawChange, ...]:
    """Read --raw --no-abbrev -z --no-renames; reject unsupported/ambiguous records."""
    if not data:
        return ()
    if not data.endswith(b"\0"):
        raise DiffParseError("truncated raw Git diff (missing NUL terminator)")
    fields = data[:-1].split(b"\0")
    if len(fields) % 2:
        raise DiffParseError("raw Git diff must contain header/path pairs")
    result = []
    seen = set()
    for header, raw_path in zip(fields[::2], fields[1::2]):
        match = _RAW_HEADER.fullmatch(header)
        if match is None:
            raise DiffParseError("unsupported raw Git diff header; rename/copy detection must be disabled")
        try:
            path = raw_path.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DiffParseError("Git filenames must be UTF-8; cannot safely represent this path") from exc
        # Git tree names are relative POSIX paths; retain spaces, tabs and newlines.
        if not path or path.startswith("/") or any(part in ("", ".", "..") for part in path.split("/")):
            raise DiffParseError("invalid repository-relative path in raw Git diff")
        if path in seen:
            raise DiffParseError(f"duplicate path in raw Git diff: {path!r}")
        seen.add(path)
        old_mode, new_mode, _, _, status = (part.decode("ascii") for part in match.groups())
        kind = _KINDS[status]
        if ((kind is ChangeKind.ADDED and (old_mode != "000000" or new_mode == "000000"))
                or (kind is ChangeKind.DELETED and (new_mode != "000000" or old_mode == "000000"))
                or (kind in (ChangeKind.MODIFIED, ChangeKind.TYPE_CHANGED)
                    and "000000" in (old_mode, new_mode))):
            raise DiffParseError("inconsistent file modes and change status")
        result.append(RawChange(path, kind, old_mode, new_mode))
    return tuple(sorted(result, key=lambda item: item.path))


def _parse_hunk(lines: list[str], index: int) -> tuple[DiffHunk, int]:
    match = _HUNK.fullmatch(lines[index])
    if match is None:
        raise DiffParseError("malformed unified diff hunk header")
    old_start = int(match[1])
    old_count = int(match[2]) if match[2] is not None else 1
    new_start = int(match[3])
    new_count = int(match[4]) if match[4] is not None else 1
    if (old_count and not old_start) or (new_count and not new_start) or not (old_count or new_count):
        raise DiffParseError("invalid hunk range")
    old_used = new_used = 0
    added = []
    removed = []
    index += 1
    marker_allowed = False
    while old_used < old_count or new_used < new_count:
        if index >= len(lines):
            raise DiffParseError("truncated hunk body")
        line = lines[index]
        if line == _NO_NEWLINE:
            if not marker_allowed:
                raise DiffParseError("unexpected no-newline marker")
            marker_allowed = False
            index += 1
            continue
        if not line or line[0] not in ("+", "-", " "):
            raise DiffParseError("hunk body does not match declared ranges")
        if line[0] in ("-", " "):
            if line[0] == "-":
                removed.append(old_start + old_used)
            old_used += 1
        if line[0] in ("+", " "):
            if line[0] == "+":
                added.append(new_start + new_used)
            new_used += 1
        if old_used > old_count or new_used > new_count:
            raise DiffParseError("hunk body exceeds declared ranges")
        marker_allowed = True
        index += 1
    if index < len(lines) and lines[index] == _NO_NEWLINE:
        index += 1
    return DiffHunk(old_start, old_count, new_start, new_count, tuple(added), tuple(removed)), index


def parse_file_patch(data: bytes) -> FilePatch:
    """Parse one ordinary Git patch. Binary evidence never yields line candidates.

    Source bytes may use any encoding. Only LF separates Git patch lines; Unicode
    line separators and carriage returns in source content are not extra lines.
    """
    lines = data.decode("utf-8", errors="surrogateescape").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines or not lines[0].startswith("diff --git "):
        raise DiffParseError("expected a one-file Git patch")
    hunks = []
    binary = False
    index = 1
    metadata = ("index ", "old mode ", "new mode ", "new file mode ",
                "deleted file mode ", "--- ", "+++ ")
    while index < len(lines):
        line = lines[index]
        if line.startswith("@@"):
            if binary:
                raise DiffParseError("patch mixes binary evidence with text hunks")
            hunk, index = _parse_hunk(lines, index)
            if hunks:
                previous = hunks[-1]
                if (hunk.old_start < previous.old_start + previous.old_count
                        or hunk.new_start < previous.new_start + previous.new_count):
                    raise DiffParseError("overlapping or out-of-order hunks")
            hunks.append(hunk)
            continue
        if line.startswith("Binary files ") and line.endswith(" differ"):
            if binary or hunks:
                raise DiffParseError("patch mixes or duplicates binary evidence")
            binary = True
        elif line.startswith(metadata):
            if hunks or binary:
                raise DiffParseError("unexpected metadata after patch body")
        else:
            raise DiffParseError("unexpected patch content or multiple files in a one-file patch")
        index += 1
    return FilePatch(tuple(hunks), binary)
