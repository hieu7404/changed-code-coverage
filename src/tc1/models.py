"""Shared immutable records. Parsing, mapping and metrics belong to later WPs.

Paths are preserved as supplied; these records do not normalize or guess matches.
Line numbers are one-based. Exclusions are separate from coverage classification.
"""

from dataclasses import dataclass
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


@dataclass(frozen=True)
class AnalysisRequest:
    repo: Path
    base: str
    head: str
    coverage: Path
    json_output: Path | None = None
    markdown_output: Path | None = None
    html_output: Path | None = None


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


@dataclass(frozen=True)
class LineCoverage:
    """One explicit instrumentation entry; absence is not a zero-hit entry."""

    location: SourceLocation
    hits: int
    condition_coverage: str | None = None
    conditions: tuple[ConditionEvidence, ...] = ()

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
class AnalysisResult:
    """Shared result container for future renderers; no metrics are computed in WP2.

Base/head are supplied revision identifiers until WP3 resolves them. Mapping and
summary contracts will be extended in their work packages before report generation.
"""

    base: str
    head: str
    lines: tuple[LineResult, ...] = ()
    branches: tuple[BranchResult, ...] = ()
    excluded_lines: tuple[ExcludedLine, ...] = ()
