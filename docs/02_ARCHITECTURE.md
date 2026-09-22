# Architecture and coverage rules

## Pipeline

```text
Git CLI -> committed diff ---------+
                                  |
Cobertura -> preserved evidence -> paths -> exclusions -> lines / branches
                                                        -> opt-in candidate model
                                                        -> shared metrics
                                                        -> JSON / Markdown / HTML
```

TC1 is a Python 3.11+ package with standard-library runtime code. Tests and coverage
collection happen outside the analyzer. The static viewer consumes an existing JSON
report, while ReportGenerator independently renders supporting collector evidence.

| Modules under `src/tc1/` | Responsibility |
| --- | --- |
| `cli.py`, `__main__.py` | Arguments, pipeline and explicit report destinations |
| `git_diff.py`, `diff_parser.py` | Git acquisition and pure raw/patch parsing |
| `cobertura.py` | XML evidence inventory |
| `path_normalizer.py`, `exclusions.py` | File identity and caller-supplied path rules |
| `matcher.py`, `branch_mapper.py`, `candidate_model.py` | Changed-line/branch findings and opt-in source-form filtering |
| `metrics.py` | One shared metric calculation |
| `models.py`, `errors.py` | Immutable records and explicit errors |
| `report_json.py`, `report_markdown.py`, `report_html.py` | Render one metrics-ready `AnalysisResult` |
| `evaluation.py` | Compare production findings with reviewed expectations |

## Git comparison

Resolve base/head to commits and require exactly one merge base. Compare merge base
to head, equivalent to `base...head`. Only added/replacement head lines become
candidates; context, deleted lines and working-tree edits do not.

TC1 detects exact-content Git renames only (`R100`). A pure rename is represented
internally with its old and new paths but has no changed head-line candidates;
therefore it cannot inflate changed-code coverage. Renames with content edits remain
deletion plus addition until a similarity policy is separately validated. Copy
detection remains disabled, so copies are additions. Binary, deleted and non-regular
files remain represented in the internal Git result without fabricated head lines.
Current public reports contain mapped findings, not a complete inventory of those
file-level limitations.

Git objects must be local. Bare repositories, non-UTF-8 filenames and ambiguous or
missing history are unsupported. Acquisition uses literal per-file paths and disables
external diff/text conversion. Large diffs have not been benchmarked.

## Cobertura evidence and paths

- The supported profile uses `coverage/packages/package/classes/class/lines/line`.
  Class filename, positive integer line number and nonnegative integer hits are required.
- Method-level entries stay separate; they never fill missing class-level evidence.
  Root summary rates do not create line hits.
- Preserve repeated records, source roots and raw branch metadata. Malformed required
  fields, unsupported structures, mixed namespaces and DOCTYPE declarations fail explicitly.
  Namespace-free and consistently namespaced XML are supported.
- Resolve paths lexically from class filenames, source roots and the repository root.
  Normalize separators and `.` / `..`; reject escapes, out-of-repository paths and
  drive-relative paths. The default model does not open source files, follow symlinks
  or guess by basename. The executable prototype reads a selected-head Git blob only
  after mapping a matching `no_explicit_line_evidence` finding.
- Windows-syntax coverage paths compare case-insensitively; POSIX syntax remains
  case-sensitive regardless of the host OS.
- Multiple classes may identify the same source file, including generated state-machine
  classes. Each changed line still needs exactly one explicit record across those classes.
  A class that can name multiple changed Git paths is ambiguous.

TC1 supports one strict JSON provenance sidecar per Cobertura export. When supplied,
it must identify the selected head commit, declare a clean worktree, and match the
coverage XML SHA-256; any mismatch fails analysis before line/branch mapping. A
successful report is `verified` only after those checks. Without a sidecar, reports
are explicitly `unverified`; `--require-provenance` rejects that mode. TC1 does not
merge multiple coverage exports.

The sidecar uses schema version `1.0` and requires `commit_sha`, `dirty_state`,
`collector`, `collector_version`, `collection_command`, `target_framework`,
`coverage_xml_sha256`, and `timestamp`. Additional collector metadata is retained
by the sidecar owner but does not weaken TC1's required checks.

## Changed lines

| Evidence at a changed head line | Status / reason |
| --- | --- |
| Exactly one reliable entry, hits > 0 | `covered` / `explicit_positive_hits` |
| Exactly one reliable entry, hits = 0 | `uncovered` / `explicit_zero_hits` |
| No matching path | `unknown` / `path_unmatched` |
| Multiple possible paths | `unknown` / `path_ambiguous` |
| No primary class line inventory | `unknown` / `class_has_no_primary_line_evidence` |
| No explicit line entry | `unknown` / `no_explicit_line_evidence` |
| Repeated same-line entries, even with equal hits | `unknown` / `ambiguous_line_evidence` |
| Unavailable file evidence | `unknown` / `file_unavailable:<reason>` |

Git candidates are not a source-language executable-line inventory. Uninstrumented
comments or braces can remain unknown; an explicitly instrumented brace is counted
according to its hits. Under the default `all_changed_lines` model, source appearance
never creates an exclusion.

The experimental `executable_prototype` runs only after mapping and only for an
`unknown/no_explicit_line_evidence` finding in UTF-8 C#. It lexically recognizes
comments, blanks, braces, using/namespace and preprocessor directives, attributes,
type/const/local declarations and signatures, control-flow labels, and multiline raw
string content. Matching forms become visible exclusions with a
`candidate_model:executable_prototype:<form>` reason. Any unrecognized source form,
explicit coverage finding, path problem, ambiguous evidence, or unsupported source
encoding remains unchanged. This is an opt-in comparison model, not a replacement
for the default denominator or a C# parser/PDB executable-line inventory.

## Exclusions

`--exclude-path` is repeatable. Patterns are repository-relative, case-sensitive and
normalize backslashes to `/`; `*` and `?` stay within one segment, while `**` crosses
segments. Absolute and parent-escaping rules are invalid. The first matching rule
wins and excludes all changed head lines in that file before line/branch mapping.

Each excluded line retains `path_rule:<pattern>` as its reason. There are no default
rules, line-range exclusions or project configuration files. Branches on excluded
lines are not mapped or assigned invented outcome counts.

Candidate-model exclusions share the visible excluded-lines inventory and metric
`excluded` count, but retain a `candidate_model:` reason rather than pretending to
be a repository path policy. They are created after mapping; default path exclusions
still run before line/branch mapping.

## Changed branches

A branch candidate requires class-level branch signal at a changed line and reliable
file identity. A usable aggregate requires exactly one line entry, `branch="true"`
and `condition-coverage="<percentage>% (<covered>/<total>)"` with valid counts.
The counts supply the aggregate; the displayed percentage is collector metadata.

TC1 reports covered/total outcomes without semantic true/false labels. Missing or
malformed aggregates, contradictory flags and repeated entries produce unknown
branch findings. A line with no branch signal, an unmatched path or method-only
evidence produces no branch candidate. `branch=false` without condition data also
produces none. Absence of candidates does not prove absence of source branches.

## Metrics

The shared summaries expose `candidates`, `classifiable`, `covered`, `uncovered`,
`unknown`, `excluded`, and `coverage_percent`. Line metrics also expose a separate
evidence-sufficiency summary: `in_scope`, `classifiable`, `classifiable_rate`, and
`unknown_rate`.

```text
classifiable = covered + uncovered
coverage_percent = 100 * covered / classifiable
classifiable_rate = 100 * classifiable / in_scope
unknown_rate = 100 * unknown / in_scope
in_scope = candidates - excluded
```

A zero denominator gives `null` / not applicable. Unknown and excluded findings
remain visible outside it. `coverage_percent` (also called classifiable coverage)
answers how much of classifiable evidence was covered; `classifiable_rate` answers
how much of the in-scope changed-line set had direct evidence, while `unknown_rate`
shows the remainder without direct evidence. For lines, each finding is one candidate and
`candidates = classifiable + unknown + excluded`.

Reliable branch aggregates contribute their outcome totals. Each unknown branch
finding contributes one visible unknown candidate; this is not an assertion that
only one outcome is unknown. Branch `excluded` is currently zero because excluded
line branches are not mapped. Branch candidate counts therefore mix known outcomes
and unknown locations and should not be read as a total source-branch inventory.

## CLI and reports

| Option | Contract |
| --- | --- |
| `--repo` | Working-tree repository; defaults to `.` |
| `--base` | Required base revision |
| `--head` | Head revision; defaults to `HEAD` |
| `--coverage` | Required Cobertura input |
| `--json`, `--markdown`, `--html` | Optional distinct output paths; parent folders are created |
| `--report-generator-html` | Optional existing supporting HTML entry page |
| `--exclude-path` | Repeatable explicit path rule |
| `--candidate-model` | `all_changed_lines` (default) or experimental `executable_prototype` |
| `--provenance` | Optional collection sidecar; a supplied sidecar must verify commit, clean worktree and XML hash |
| `--require-provenance` | Reject analysis unless a supplied sidecar verifies |

All file arguments resolve from the caller's working directory, independently of
`--repo`. With no destinations, analysis runs without writing a report or printing
a coverage summary. Successful analysis/help/version exit 0; expected input/write
errors exit 1; invalid CLI usage exits 2. Coverage levels do not change the exit code.

JSON schema `1.3` contains `analysis.base`, `analysis.head`, `analysis.candidate_model`, provenance status,
line/branch `metrics`,
line evidence sufficiency, `lines`, `excluded_lines`, `branches`, and optional
`supporting_evidence`. The reported base is the resolved supplied base commit; the
actual merge base remains internal to Git acquisition. Findings retain path, line,
reason and available hits or branch aggregates. No source text or full changed-file
inventory is exported.

All renderers consume the same stored summaries. HTML is standalone UTF-8 with
escaped evidence text; Markdown escapes table content. ReportGenerator links are
output-relative where possible, with visible availability. TC1 does not generate,
copy or guess that HTML. Output writes are individual files, not a multi-file transaction.

## Generated output policy

| Location | Contents |
| --- | --- |
| `artifacts/tc1/` | TC1 reports, selected Cobertura and collection metadata |
| `artifacts/tc1/coverage/` | ReportGenerator bundle |
| `artifacts/test-results/` | Raw collection evidence, logs and test results |
| `artifacts/eval/<run-id>/` | Generated evaluation results and observations |
| `artifacts/tools/` | Optional local tool installations and caches |

`artifacts/` is gitignored. Build intermediates may use standard ignored locations.
Only reviewed deterministic inputs and expectations belong in `fixtures/` and `eval/`;
setup, semantics and durable evidence summaries belong in documentation.
