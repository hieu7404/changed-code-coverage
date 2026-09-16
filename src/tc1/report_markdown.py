"""Render one metrics-ready analysis result as readable Markdown."""

from __future__ import annotations

from tc1.errors import ModelValidationError
from tc1.models import AnalysisResult, CoverageSummary


def _text(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def _percentage(summary: CoverageSummary) -> str:
    return "N/A" if summary.coverage_percent is None else f"{summary.coverage_percent:.2f}%"


def _summary(title: str, summary: CoverageSummary) -> list[str]:
    return [
        f"## {title}",
        "",
        "| Candidates | Classifiable | Covered | Uncovered | Unknown | Excluded | Coverage |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| {summary.candidates} | {summary.classifiable} | {summary.covered} | "
        f"{summary.uncovered} | {summary.unknown} | {summary.excluded} | {_percentage(summary)} |",
        "",
    ]


def render_markdown(
    analysis: AnalysisResult, *, report_generator_html: str | None = None,
    report_generator_available: bool = False,
) -> str:
    """Return a deterministic Markdown report without re-deriving metrics."""
    if analysis.metrics is None:
        raise ModelValidationError("reports require AnalysisResult.metrics")

    lines = [
        "# TC1 Changed-Code Coverage Report",
        "",
        f"- Base: `{_text(analysis.base)}`",
        f"- Head: `{_text(analysis.head)}`",
        "",
    ]
    lines.extend(_summary("Changed Lines", analysis.metrics.lines))
    lines.extend(_summary("Changed Branches", analysis.metrics.branches))
    lines.extend([
        "## Line Findings",
        "",
        "| Path | Line | Status | Hits | Reason |",
        "| --- | ---: | --- | ---: | --- |",
    ])
    if analysis.lines:
        lines.extend(
            f"| `{_text(item.location.path)}` | {item.location.line} | {item.status.value} | "
            f"{'' if item.hits is None else item.hits} | `{_text(item.reason)}` |"
            for item in analysis.lines
        )
    else:
        lines.append("| — | — | — | — | No changed-line findings |")
    lines.extend(["", "## Excluded Lines", "", "| Path | Line | Reason |", "| --- | ---: | --- |"])
    if analysis.excluded_lines:
        lines.extend(
            f"| `{_text(item.location.path)}` | {item.location.line} | `{_text(item.reason)}` |"
            for item in analysis.excluded_lines
        )
    else:
        lines.append("| — | — | No excluded-line findings |")
    lines.extend(["", "## Branch Findings", "", "| Path | Line | Covered / Total | Reason |", "| --- | ---: | ---: | --- |"])
    if analysis.branches:
        for item in analysis.branches:
            aggregate = "unknown" if item.aggregate is None else f"{item.aggregate.covered} / {item.aggregate.total}"
            lines.append(
                f"| `{_text(item.location.path)}` | {item.location.line} | {aggregate} | `{_text(item.reason)}` |"
            )
    else:
        lines.append("| — | — | — | No changed-branch findings |")
    lines.extend(["", "## Supporting Evidence", ""])
    if report_generator_html is None:
        lines.append("ReportGenerator coverage HTML was not requested for this report.")
    elif report_generator_available:
        lines.append(f"[Open ReportGenerator coverage HTML]({_text(report_generator_html)})")
    else:
        lines.append(f"ReportGenerator coverage HTML is unavailable (expected `{_text(report_generator_html)}`).")
    return "\n".join(lines) + "\n"
