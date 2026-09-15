# Fixtures

Small deterministic fixtures used by TC1 tests.

Current diff fixtures and future coverage fixture layout:

```text
fixtures/
├── diffs/
├── cobertura/
└── expected/
```

Fixtures should be small, readable, and committed.

WP3 adds eight one-file patches under `diffs/` with reviewed ranges, head-line
candidates and removed lines in `expected/git_diff.json`. They cover multiple
hunks, additions, deletions, deletion-only edits, missing final newline markers,
binary output, empty additions and mode-only changes. These are synthetic Git
evidence fixtures; source text is not claimed to be executable C#.
See [WP3 validation](../docs/15_GIT_DIFF_PARSER.md).

Each patch is parsed with its own raw-inventory path in production. Tests of
multiple files, revisions and literal filenames use isolated Git repositories
under `artifacts/test-results/pytest-tmp/`. Patch fixtures are kept at LF by
`.gitattributes` to match Git's patch output on all hosts.

All generated run output goes under the repository-root `artifacts/`, regardless of size.
Only small inputs and expected results deliberately reviewed as deterministic fixtures
belong here. See [Generated output policy](../docs/03_ARCHITECTURE.md#generated-output-policy).
