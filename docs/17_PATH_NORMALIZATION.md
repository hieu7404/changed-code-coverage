# WP5 Path Normalization

## Status

**WP5 complete.** The resolver was validated with focused pytest cases on Windows.
It combines Git paths with Cobertura source-root/class-filename evidence without
classifying lines, calculating metrics, emitting reports, or inspecting source files.

## API

```python
from tc1.path_normalizer import match_coverage_paths

matches = match_coverage_paths(coverage_report, changed_git_paths, repo_root)
```

`match_coverage_paths` returns one immutable `PathMatch` per Git path, in input order.

## Rules

- Git paths must be non-empty and repository-relative. They use `/`; `.` and `..`
  are collapsed lexically.
- Relative Cobertura filenames are joined to every declared source root. With no
  source, or an explicitly empty source, the filename is repo-relative.
- Absolute filenames are self-contained; source roots are not appended to them.
- `/` and `\\` normalize to `/`. POSIX and drive/UNC absolute paths are recognized
  independently of the host OS.
- Escaping/out-of-repository paths and drive-relative paths such as `C:File.cs`
  have no candidate. There is no basename fallback or source-file lookup.
- Windows-syntax coverage evidence compares case-insensitively. POSIX-syntax evidence
  stays case-sensitive even when TC1 runs on Windows; case collisions are ambiguous.

`matched` means exactly one Cobertura class record names exactly one changed Git path.
`unmatched` means no class record names it. `ambiguous` means one class can name
multiple Git paths, or multiple class records name one Git path. Only `matched` is
usable by WP6; all other statuses must become `unknown`, never `uncovered`.

## Historical CLI boundary

`tc1 analyze` now resolves Git revisions, parses Cobertura and runs the path-only
resolver before its explicit WP6-WP9 not-implemented error. It writes no report.

## Validation

```powershell
.venv/Scripts/python.exe -m pytest tests/test_path_normalizer.py -q
.venv/Scripts/python.exe -m pytest
git diff --check
```

Focused cases cover Windows/POSIX syntax, source roots, absolute and relative paths,
path escapes, duplicate classes, multiple candidates and case collisions.

## Limitations

- Resolution is lexical: it does not follow symlinks or open files.
- Conflicting line evidence inside a matched class remains for WP6 to resolve.

Next bounded step: **WP6 line mapper**.
