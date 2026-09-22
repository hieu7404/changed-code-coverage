"""Shared immutable records. Parsing and mapping populate the metrics-ready result.

Paths are preserved as supplied; these records do not normalize or guess matches.
Line numbers are one-based. Exclusions are separate from coverage classification.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from tc1.errors import ModelValidationError


def _count(name: str, value: int, minimum: int = 0) -> None:
    if type(value) is not int or value < minimum:
        raise ModelValidationError(f"{name} must be an integer >= {minimum}")


def _text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ModelValidationError(f"{name} must be a non-empty string")


class CoverageStatus(StrEnum):
    COVERED = "covered"
    UNCOVERED = "uncovered"
    UNKNOWN = "unknown"


class CandidateModel(StrEnum):
    """How TC1 selects changed lines for its visible denominator."""

    ALL_CHANGED_LINES = "all_changed_lines"
    EXECUTABLE_PROTOTYPE = "executable_prototype"


@dataclass(frozen=True)
class AnalysisRequest:
    repo: Path
    base: str
    head: str
    coverage: Path
    json_output: Path | None = None
    markdown_output: Path | None = None
    html_output: Path | None = None
    report_generator_html: Path | None = None
    exclude_paths: tuple[str, ...] = ()
    provenance: Path | None = None
    require_provenance: bool = False
    candidate_model: CandidateModel = CandidateModel.ALL_CHANGED_LINES


@dataclass(frozen=True)
class CoverageProvenance:
    """Verified metadata for the one Cobertura export used by an analysis."""

    commit_sha: str
    dirty_state: bool
    collector: str
    collector_version: str
    collection_command: str
    target_framework: str
    coverage_xml_sha256: str
    timestamp: str

    def __post_init__(self) -> None:
        for name in (
            "commit_sha", "collector", "collector_version", "collection_command",
            "target_framework", "coverage_xml_sha256", "timestamp",
        ):
            _text(name, getattr(self, name))
        if type(self.dirty_state) is not bool:
            raise ModelValidationError("dirty_state must be a boolean")


@dataclass(frozen=True)
class SourceLocation:
    path: str
    line: int

    def __post_init__(self) -> None:
        _text("path", self.path)
        _count("line", self.line, minimum=1)


@dataclass(frozen=True)
class ConditionEvidence:
    """Opaque collector attributes, including IDs with no semantic true/false meaning."""

    number: str | None = None
    type: str | None = None
    coverage: str | None = None
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class LineCoverage:
    """One explicit instrumentation entry; absence is not a zero-hit entry."""

    location: SourceLocation
    hits: int
    condition_coverage: str | None = None
    conditions: tuple[ConditionEvidence, ...] = ()
    branch: str | None = None
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _count("hits", self.hits)


@dataclass(frozen=True)
class BranchAggregate:
    """Reliable outcome counts at a location, without semantic branch identities."""

    covered: int
    total: int

    def __post_init__(self) -> None:
        _count("covered", self.covered)
        _count("total", self.total, minimum=1)
        if self.covered > self.total:
            raise ModelValidationError("covered branch outcomes cannot exceed total")


@dataclass(frozen=True)
class LineResult:
    location: SourceLocation
    status: CoverageStatus
    reason: str
    hits: int | None = None

    def __post_init__(self) -> None:
        _text("reason", self.reason)
        if not isinstance(self.status, CoverageStatus):
            raise ModelValidationError("status must be a CoverageStatus")
        if self.hits is not None:
            _count("hits", self.hits)
        if self.status is CoverageStatus.COVERED and (self.hits is None or self.hits == 0):
            raise ModelValidationError("covered lines require explicit hits > 0")
        if self.status is CoverageStatus.UNCOVERED and self.hits != 0:
            raise ModelValidationError("uncovered lines require explicit hits = 0")


@dataclass(frozen=True)
class BranchResult:
    """An aggregate at a changed location, or unknown when aggregate is None.

Unknown locations do not assert a known number of missing branch outcomes.
"""

    location: SourceLocation
    reason: str
    aggregate: BranchAggregate | None = None

    def __post_init__(self) -> None:
        _text("reason", self.reason)


@dataclass(frozen=True)
class ExcludedLine:
    location: SourceLocation
    reason: str

    def __post_init__(self) -> None:
        _text("reason", self.reason)


@dataclass(frozen=True)
class CoverageSummary:
    """One changed-code coverage summary with a visible evidence breakdown.

    ``coverage_percent`` is derived from classifiable outcomes only. Unknown and
    excluded findings remain candidates but never enter that denominator.
    """

    candidates: int
    classifiable: int
    covered: int
    uncovered: int
    unknown: int
    excluded: int
    coverage_percent: float | None = field(init=False)

    def __post_init__(self) -> None:
        for name in ("candidates", "classifiable", "covered", "uncovered", "unknown", "excluded"):
            _count(name, getattr(self, name))
        if self.classifiable != self.covered + self.uncovered:
            raise ModelValidationError("classifiable must equal covered + uncovered")
        if self.candidates != self.classifiable + self.unknown + self.excluded:
            raise ModelValidationError("candidates must equal classifiable + unknown + excluded")
        percent = None if self.classifiable == 0 else (100 * self.covered / self.classifiable)
        object.__setattr__(self, "coverage_percent", percent)


@dataclass(frozen=True)
class LineEvidenceSufficiency:
    """How much of the in-scope changed-line set has classifiable evidence.

    This is deliberately line-specific. Branch candidate counts can combine
    collector outcome totals with unknown locations, so they are not a source
    branch inventory suitable for an analogous rate.
    """

    in_scope: int
    classifiable: int
    classifiable_rate: float | None = field(init=False)
    unknown_rate: float | None = field(init=False)

    def __post_init__(self) -> None:
        _count("in_scope", self.in_scope)
        _count("classifiable", self.classifiable)
        if self.classifiable > self.in_scope:
            raise ModelValidationError("classifiable line evidence cannot exceed in_scope")
        rate = None if self.in_scope == 0 else (100 * self.classifiable / self.in_scope)
        object.__setattr__(self, "classifiable_rate", rate)
        unknown_rate = None if self.in_scope == 0 else (100 * (self.in_scope - self.classifiable) / self.in_scope)
        object.__setattr__(self, "unknown_rate", unknown_rate)


@dataclass(frozen=True)
class AnalysisMetrics:
    """Coverage summaries and line-evidence sufficiency from one result."""

    lines: CoverageSummary
    branches: CoverageSummary
    line_evidence: LineEvidenceSufficiency

    def __post_init__(self) -> None:
        if not isinstance(self.lines, CoverageSummary):
            raise ModelValidationError("lines must be a CoverageSummary")
        if not isinstance(self.branches, CoverageSummary):
            raise ModelValidationError("branches must be a CoverageSummary")
        if not isinstance(self.line_evidence, LineEvidenceSufficiency):
            raise ModelValidationError("line_evidence must be a LineEvidenceSufficiency")
        if self.line_evidence.in_scope != self.lines.candidates - self.lines.excluded:
            raise ModelValidationError("line evidence in_scope must equal line candidates minus exclusions")
        if self.line_evidence.classifiable != self.lines.classifiable:
            raise ModelValidationError("line evidence classifiable must equal line summary classifiable")


@dataclass(frozen=True)
class AnalysisResult:
    """Shared result container for metrics and future renderers.

    Base/head are supplied revision identifiers until WP3 resolves them. Mapping,
    metrics, and all future renderers share this immutable record.
    """

    base: str
    head: str
    lines: tuple[LineResult, ...] = ()
    branches: tuple[BranchResult, ...] = ()
    excluded_lines: tuple[ExcludedLine, ...] = ()
    metrics: AnalysisMetrics | None = None
    provenance: CoverageProvenance | None = None
    candidate_model: CandidateModel = CandidateModel.ALL_CHANGED_LINES

    def __post_init__(self) -> None:
        if self.metrics is not None and not isinstance(self.metrics, AnalysisMetrics):
            raise ModelValidationError("metrics must be an AnalysisMetrics or None")
        if self.provenance is not None and not isinstance(self.provenance, CoverageProvenance):
            raise ModelValidationError("provenance must be a CoverageProvenance or None")
        if not isinstance(self.candidate_model, CandidateModel):
            raise ModelValidationError("candidate_model must be a CandidateModel")


class ChangeKind(StrEnum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    TYPE_CHANGED = "type_changed"
    RENAMED = "renamed"


@dataclass(frozen=True)
class DiffHunk:
    """Validated coordinates; added lines use head numbering, removed lines use merge-base."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    added_lines: tuple[int, ...] = ()
    removed_lines: tuple[int, ...] = ()


@dataclass(frozen=True)
class FileChange:
    """Git evidence only. Unavailable reasons are not coverage exclusions."""

    path: str
    kind: ChangeKind
    old_mode: str
    new_mode: str
    hunks: tuple[DiffHunk, ...] = ()
    is_binary: bool = False
    unavailable_reason: str | None = None
    old_path: str | None = None

    @property
    def changed_lines(self) -> tuple[int, ...]:
        return tuple(line for hunk in self.hunks for line in hunk.added_lines)


@dataclass(frozen=True)
class GitDiffResult:
    repo_root: Path
    base_commit: str
    head_commit: str
    merge_base: str
    files: tuple[FileChange, ...] = ()


@dataclass(frozen=True)
class CoverageMethod:
    """Supporting method evidence; never added to the class-level line inventory."""

    name: str | None = None
    signature: str | None = None
    lines: tuple[LineCoverage, ...] = ()
    lines_present: bool = False
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class CoverageClass:
    filename: str
    name: str | None = None
    lines: tuple[LineCoverage, ...] = ()
    methods: tuple[CoverageMethod, ...] = ()
    lines_present: bool = False
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class CoveragePackage:
    name: str | None = None
    classes: tuple[CoverageClass, ...] = ()
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class CoverageReport:
    """Raw export inventory, not classified coverage or a report summary.

    Document order and duplicate records are retained. Neither convenience property
    merges or deduplicates evidence; future mapping must resolve ambiguity explicitly.
    """

    sources: tuple[str, ...] = ()
    packages: tuple[CoveragePackage, ...] = ()
    attributes: tuple[tuple[str, str], ...] = ()

    @property
    def classes(self) -> tuple[CoverageClass, ...]:
        return tuple(item for package in self.packages for item in package.classes)

    @property
    def line_entries(self) -> tuple[LineCoverage, ...]:
        return tuple(line for item in self.classes for line in item.lines)
