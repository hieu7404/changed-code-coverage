# WP4 Cobertura Parser

## Status

**WP4 complete.** Validated on Windows / Python 3.14.6 with pytest 9.1.1:
166 total Python tests pass. The parser also reproduces the recorded WP1 export's
12 class-level entries, their hit counts, and three sets of branch metadata.

Git rename/copy behavior remains `--no-renames`, as confirmed by the user when
starting WP4. WP3 was committed as `1079721`.

> Current CLI behavior is documented in [WP9 reports](21_REPORTS.md). This document retains the WP4 implementation boundary and validation evidence.

WP4 acquires coverage evidence. Path matching, classifications, branch mapping,
denominators and reports are completed in later work packages; see [WP9 reports](21_REPORTS.md).

## API and input contract

```python
from pathlib import Path
from tc1.cobertura import read_cobertura, parse_cobertura

coverage = read_cobertura(Path("artifacts/tc1/coverage.cobertura.xml"))
# For callers that already have XML bytes:
same_coverage = parse_cobertura(
    Path("artifacts/tc1/coverage.cobertura.xml").read_bytes()
)
assert coverage == same_coverage

for entry in coverage.line_entries:
    print(entry.location.path, entry.location.line, entry.hits,
          entry.branch, entry.condition_coverage)
```

`read_cobertura` reads one local file. Relative input paths are relative to the
calling process's working directory, independently of `--repo`.
`parse_cobertura` accepts XML bytes and honors the XML encoding declaration.

The module uses the standard-library ElementTree parser. No additional runtime
dependency, source-file lookup, collector execution, path normalization, or network
access is needed. Input bytes are not rewritten.

## Supported XML profile

The controlled profile accepts:

```text
coverage
  sources/source                       optional
  packages/package/classes/class       packages and each classes container required
    methods/method/lines/line           optional supporting evidence
    lines/line                         optional primary evidence
      conditions/condition             optional raw branch metadata
```

Both namespace-free XML and a consistently namespaced document are supported.
Unexpected elements, mixed namespace structures, repeated singleton containers and
unexpected structural text are errors. This avoids quietly accepting misplaced line
evidence. Empty `<coverage><packages/></coverage>` is a valid empty inventory;
`<coverage/>` alone is outside this profile.

A class requires a non-blank `filename`. Each explicit line requires:

- `number`: ASCII decimal digits representing an integer >= 1;
- `hits`: ASCII decimal digits representing an integer >= 0.

Missing, negative, fractional or otherwise invalid required values fail the parse.
Leading zeroes are accepted; their raw attribute text is retained. Missing class or
method `lines` containers remain distinguishable from present-but-empty containers.

DOCTYPE declarations, including external DTD references, are explicitly unsupported
and rejected before DTD-supplied evidence is expanded. The validated Coverlet export
does not use a DTD. This is a defined collector profile, not complete Cobertura DTD
validation. Additional collector profiles need fixtures before compatibility is claimed.

## Evidence preservation

| Model | Responsibility |
| --- | --- |
| `CoverageReport` | Source-root strings, packages and root attributes |
| `CoveragePackage` | Package name, classes and attributes |
| `CoverageClass` | Filename, class name, primary lines, methods, lines-container presence and attributes |
| `CoverageMethod` | Method name/signature and supporting line evidence |
| `LineCoverage` | Source location, explicit hits, raw branch flag, condition text and attributes |
| `ConditionEvidence` | Optional number/type/coverage strings and attributes |

Records are frozen dataclasses with tuple collections. Package, class, method,
line and condition order follows the document. Attribute pairs are sorted for
stable comparison. Attributes on coverage/package/class/method/line/condition
elements remain available, including custom attributes and exporter summary rates.
Rates are not used to manufacture line hits or calculate TC1 metrics.

Source-root strings and filenames are retained as decoded XML values. They are not
trimmed, joined, slash-normalized or matched by basename. Empty source strings remain
visible. WP5 will determine reliable path matches.

`CoverageReport.classes` flattens classes across packages.
`CoverageReport.line_entries` flattens **only class-level** lines. Both are raw
inventory views; neither deduplicates, aggregates nor assigns coverage states.

### Class and method duplication

The WP1 Coverlet export repeats its 12 line entries under both class and method.
WP4 returns 12 primary entries, with 12 method entries retained separately.
Method entries are never added to the primary inventory.

If a class has only method evidence, its primary line list stays empty and
`lines_present=False`. There is no method-to-class fallback. Conflicting method
evidence remains available for later reliability checks.

### Repeated filenames or line numbers

Repeated entries within a class, across classes, or across packages are all retained.
The parser does not overwrite by filename/line, sum hits, take a maximum, or silently
choose the first record. The mapper must resolve such evidence or report unknown.
Identical records also remain separate until an explicit deduplication policy exists.

### Missing and ambiguous evidence

Missing line entries do not become zero-hit records. A missing required attribute
on an existing line is malformed input and produces an error.

Optional `branch`, `condition-coverage` and condition attributes remain raw,
including absent, incomplete or contradictory values. For example, `branch="maybe"`
or `condition-coverage="not measured"` does not invalidate a valid line hit count,
but cannot establish reliable branch coverage.

No semantic true/false branch identities or covered/total aggregates are derived in
WP4. Branch interpretation belongs to WP7. Unknown and excluded items must remain
visible outside the classifiable denominator when WP6-WP8 are implemented.

## Historical CLI behavior

The existing command now performs:

```text
resolve/read Git changes
  -> read/parse Cobertura
  -> explicit stop before WP5-WP9
```

```powershell
.venv/Scripts/python.exe -m tc1 analyze --repo . --base HEAD~1 --head HEAD --coverage artifacts/tc1/coverage.cobertura.xml
```

Repository/revision failures occur first. Unreadable or malformed coverage produces
`CoberturaError` (an `InputError`) with file context, stderr output and exit 1.

When both inputs are read successfully, the CLI prints their file/entry counts as
part of an explicit not-implemented error and exits 1. These are raw record counts,
not changed-code coverage results. No report is created or overwritten.
Help/version still exit 0; invalid CLI usage exits 2.

Reading both inputs does not prove that the export belongs to the selected Git head.
Coverage provenance, file matching and final classification remain later pipeline work.

## Validation

```powershell
.venv/Scripts/python.exe -m pytest --junitxml=artifacts/test-results/wp4/pytest.xml
git diff --check
```

- Five reviewed XML fixtures live under `fixtures/cobertura/`, with sample
  expectations in `fixtures/expected/cobertura.json`.
- The portable sample fixture retains the WP1 line/branch evidence with a relative
  filename, source root `.`, and fixed timestamp; it is not the original raw export.
- Tests cover exact hits, class/method separation, duplicates, missing/empty evidence,
  source strings, raw branch/custom metadata, namespaces, XML encodings, invalid
  numeric data, unsupported structure/DTD, file errors and CLI artifact preservation.
- The complete Python suite passes: **166 tests**. JUnit evidence:
  `artifacts/test-results/wp4/pytest.xml`.
- The actual WP1 export yields 12 primary entries: 10 positive-hit and 2 zero-hit.
  Its 12 method entries remain separate; metadata at lines 8, 13 and 19 matches WP1.
  Input SHA-256 remains unchanged, and the CLI creates no report. Evidence:
  `artifacts/test-results/wp4/baseline-check.json`.
- The actual-workspace CLI check needed a process-local Git ownership exception.
  No persistent Git configuration was changed.
- C# source, tests and coverage collection were unchanged and not rerun.

The parser holds the XML tree and result inventory in memory. Large exports and
other operating systems have not been benchmarked/validated. There is no coverage
classification or percentage calculation in this work package.

Next bounded step: **WP5 path normalization**, with explicit ambiguity detection
between Git paths and Cobertura source-root/filename evidence.
