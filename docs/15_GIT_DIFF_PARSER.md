# WP3 Git Diff Parser

## Status

This document records WP3 behavior. WP4 now also reads Cobertura;
see [current input and CLI behavior](16_COBERTURA_PARSER.md).

**WP3 complete.** Validated on Windows with Python 3.14.6, Git 2.55.0 and
pytest 9.1.1. The full Python suite has 104 passing cases.

WP3 identifies changed source-line candidates. It does not decide whether a line
is executable, covered, uncovered, unknown, or excluded. Coverage analysis and
reports remain WP4-WP9.

## Comparison contract

`read_git_diff(repo, base, head="HEAD")`:

1. Require a Git working-tree repository; a subdirectory is resolved to its root.
2. Resolve each revision to a full commit ID, including annotated tags.
3. Require exactly one merge base.
4. Compare that merge base to the resolved head commit.

This is the intended `git diff base...head` comparison. If base has changes on a
separate branch after the common ancestor, those base-only changes are not treated
as head changes. Both supplied commits and the actual merge base remain in the
result. Invalid refs, non-commit objects, unrelated/incomplete history and multiple
merge bases produce errors; the tool does not choose a fallback comparison.

Only committed trees are compared. Staged, unstaged and untracked changes do not
alter the result, and the module does not check out revisions or modify the index.
Matching a coverage export to the selected head remains a later pipeline concern.

## Acquisition and parsing

`git_diff.py` runs the Git CLI with argument lists and a 30-second timeout per
command. It obtains a NUL-delimited raw file inventory, then a separate patch for
each supported path using literal pathspecs. This avoids parsing filenames out of
quoted or space-delimited patch headers.

The diff explicitly disables rename detection, external diff and text conversion,
color and relative-path output. It fixes zero context, zero inter-hunk context and
the Myers diff algorithm. Repository-routing environment variables and
`GIT_DIFF_OPTS` do not override the requested repository/context. Lazy fetching is
disabled; Git must have the required objects locally. Git ownership checks remain
in effect; the engine does not add trust exceptions or change global configuration.

`diff_parser.py` contains pure parsers:

- `parse_raw_diff(bytes)`: supported statuses, exact paths, file modes, stable path ordering.
- `parse_file_patch(bytes)`: one-file hunks and binary markers, with body/range validation.

Multiple files are represented by the inventory and their individual patches.
The patch parser intentionally rejects combined merge patches and concatenated
multi-file patches. It is not a general-purpose parser for arbitrary patch formats.

Filename bytes must be UTF-8. Spaces, non-ASCII text and pathspec metacharacters
are preserved; no basename matching or path normalization is attempted here.
Source content may use other encodings because only Git line markers are inspected.
LF separates patch lines; embedded Unicode separators and source CR bytes do not
create extra source lines.

## Shared Git models

| Model | Contents |
| --- | --- |
| `GitDiffResult` | Repository root, resolved base/head, merge base, sorted file changes |
| `FileChange` | Path, change kind, old/new modes, hunks, binary flag, optional unavailable reason |
| `DiffHunk` | Old/new ranges, added head-line numbers, removed merge-base-line numbers |
| `ChangeKind` | Added, modified, deleted, type changed |

`FileChange.changed_lines` flattens only added lines from all hunks. Replacements
therefore contribute their new lines; unchanged context and old removed lines do
not enter the head candidate list. This is Git evidence for the future
`AnalysisResult`, not a separate coverage report or denominator calculation.

## Explicit cases and limitations

| Case | WP3 behavior |
| --- | --- |
| Modified text | Added/replacement head lines, with all hunks retained |
| Added text | All added lines; an empty added file remains visible with no lines |
| Deletion-only edit | Modified file with removed-line evidence and no new candidates |
| Deleted file | Visible as deleted, reason `deleted_file`; no head lines |
| Binary file | Binary flag and reason `binary_file`; no fabricated source lines |
| Deleted binary | Deleted reason plus binary flag |
| File mode change only | Old/new modes retained, no changed source lines |
| Symlink, gitlink/submodule, unsupported type transition | Visible with reason `unsupported_file_type`; not parsed as ordinary source |
| Rename | Deleted old path plus added new path; all new-path lines can be candidates |
| Copy | Added destination; no source/destination identity inferred |
| Equal trees | Empty file tuple is a valid result |
| Invalid/malformed evidence | Explicit `GitDiffError` or `DiffParseError` |

Unavailable reasons are not automatic TC1 exclusions and are not coverage results.
A deleted non-regular file is identified by its deleted kind and unsupported-type
reason. No C# extension filter is applied yet; later mapping must establish explicit
scope/exclusion rules. Rename/copy treatment can increase line candidates relative
to a rename-aware comparison; that limitation is intentional and visible here.

The initial implementation runs one Git process per supported changed file, in
addition to repository/revision/inventory commands. Large diffs have not been
benchmarked. Bare repositories and non-UTF-8 filenames are not supported.
Windows was exercised; other operating systems have not been validated.

## Use

Install the package as described in [WP2 setup](14_PYTHON_BOOTSTRAP.md).
From Python:

```python
from pathlib import Path
from tc1.git_diff import read_git_diff

changes = read_git_diff(Path("."), base="HEAD~1", head="HEAD")
print(changes.base_commit, changes.head_commit, changes.merge_base)
for change in changes.files:
    print(change.path, change.kind, change.changed_lines, change.unavailable_reason)
```

The existing `tc1 analyze` command now resolves and reads Git changes. Input
failures are shown on stderr with exit 1. If Git succeeds, it reports the changed
file count and explicitly stops with exit 1 because coverage/report stages are
not implemented. It does not read the coverage file or create/overwrite reports.

```powershell
.venv/Scripts/python.exe -m tc1 analyze --repo . --base HEAD~1 --head HEAD --coverage artifacts/tc1/coverage.cobertura.xml
```

Help/version still exit 0; malformed CLI usage exits 2. There is no blocking
coverage threshold or CI integration.

## Validation and reproducibility

```powershell
.venv/Scripts/python.exe -m pytest --junitxml=artifacts/test-results/wp3/pytest.xml
git diff --check
```

- Eight reviewed patch fixtures plus explicit expectations live in
  `fixtures/diffs/` and `fixtures/expected/git_diff.json`.
  `.gitattributes` keeps patch fixture line endings at LF across checkouts.
- Tests cover multiple files/hunks, added/deleted/binary/empty files, unusual paths,
  malformed evidence, missing final newlines, raw condition-independent Git data,
  source control characters, mode/type changes, annotated tags, divergent branches,
  unrelated/ambiguous history, dirty working trees, CLI failures and Git launch failures.
- Temporary test repositories are created only under pytest's artifact scratch area.
  Tests isolate user Git configuration and require an installed Git executable.
- The full suite passes: **104 tests**. JUnit evidence:
  `artifacts/test-results/wp3/pytest.xml`.
- A sampled actual-repository check compares WP1 commit `f24c137` to WP2 commit
  `b634899`: 17 changed files, including added `src/tc1/cli.py` at head lines 1-61.
  CLI exit behavior and unchanged Git status were also verified. Evidence:
  `artifacts/test-results/wp3/actual-repo-check.json`.
  This shared workspace required a process-local ownership exception for that check;
  no persistent Git configuration was written.
- C# source/tests and coverage collection were unchanged and not rerun.

Next bounded step: **WP4 Cobertura parser** — preserve explicit hits and branch
metadata, handle malformed XML, and retain missing/unreliable evidence as unknown
when the mapper is implemented.
