"""Render one metrics-ready analysis result as standalone, escaped HTML."""

from __future__ import annotations

from html import escape

from tc1.errors import ModelValidationError
from tc1.models import AnalysisResult, CoverageSummary, LineEvidenceSufficiency


def _percentage(summary: CoverageSummary) -> str:
    return "N/A" if summary.coverage_percent is None else f"{summary.coverage_percent:.2f}%"


def _summary(title: str, summary: CoverageSummary) -> str:
    values = (summary.candidates, summary.classifiable, summary.covered, summary.uncovered,
              summary.unknown, summary.excluded, _percentage(summary))
    headers = ("Candidates", "Classifiable", "Covered", "Uncovered", "Unknown", "Excluded", "Coverage")
    return (
        f"<section><h2>{escape(title)}</h2><table><thead><tr>"
        + "".join(f"<th>{header}</th>" for header in headers)
        + "</tr></thead><tbody><tr>"
        + "".join(f"<td>{value}</td>" for value in values)
        + "</tr></tbody></table></section>"
    )


def _line_evidence(summary: CoverageSummary, evidence: LineEvidenceSufficiency) -> str:
    rate = "N/A" if evidence.classifiable_rate is None else f"{evidence.classifiable_rate:.2f}%"
    unknown_rate = "N/A" if evidence.unknown_rate is None else f"{evidence.unknown_rate:.2f}%"
    return (
        "<p><strong>Changed-code coverage:</strong> " + _percentage(summary) + ".<br>"
        "<strong>Evidence available for:</strong> " + rate + " of in-scope changed lines "
        f"({evidence.classifiable} / {evidence.in_scope}).<br>"
        f"<strong>Unknown evidence:</strong> {unknown_rate} of in-scope changed lines.</p>"
    )


def _cell(value: object) -> str:
    return escape(str(value))


def render_html(
    analysis: AnalysisResult, *, report_generator_html: str | None = None,
    report_generator_available: bool = False,
) -> str:
    """Return standalone HTML; all evidence-derived text is escaped."""
    if analysis.metrics is None:
        raise ModelValidationError("reports require AnalysisResult.metrics")
    line_rows = "".join(
        "<tr>"
        f"<td>{_cell(item.location.path)}</td><td>{item.location.line}</td>"
        f"<td>{_cell(item.status.value)}</td><td>{'' if item.hits is None else item.hits}</td>"
        f"<td>{_cell(item.reason)}</td></tr>"
        for item in analysis.lines
    ) or "<tr><td colspan=\"5\">No changed-line findings</td></tr>"
    excluded_rows = "".join(
        f"<tr><td>{_cell(item.location.path)}</td><td>{item.location.line}</td><td>{_cell(item.reason)}</td></tr>"
        for item in analysis.excluded_lines
    ) or "<tr><td colspan=\"3\">No excluded-line findings</td></tr>"
    branch_rows = "".join(
        "<tr>"
        f"<td>{_cell(item.location.path)}</td><td>{item.location.line}</td>"
        f"<td>{'unknown' if item.aggregate is None else f'{item.aggregate.covered} / {item.aggregate.total}'}</td>"
        f"<td>{_cell(item.reason)}</td></tr>"
        for item in analysis.branches
    ) or "<tr><td colspan=\"4\">No changed-branch findings</td></tr>"
    if report_generator_html is None:
        evidence = "<p>ReportGenerator coverage HTML was not requested for this report.</p>"
    elif report_generator_available:
        evidence = f'<p><a href="{escape(report_generator_html, quote=True)}">Open ReportGenerator coverage HTML</a></p>'
    else:
        evidence = f"<p>ReportGenerator coverage HTML is unavailable (expected <code>{_cell(report_generator_html)}</code>).</p>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TC1 Changed-Code Coverage Report</title>
  <style>body{{font-family:system-ui,sans-serif;margin:2rem;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin-bottom:1.5rem}}th,td{{border:1px solid #d1d5db;padding:.5rem;text-align:left}}th{{background:#f3f4f6}}td{{vertical-align:top}}code{{word-break:break-word}}</style>
</head>
<body>
  <h1>TC1 Changed-Code Coverage Report</h1>
  <p>Base: <code>{_cell(analysis.base)}</code><br>Head: <code>{_cell(analysis.head)}</code><br>Coverage provenance: <strong>{"unverified" if analysis.provenance is None else "verified"}</strong>{"" if analysis.provenance is None else f' (commit <code>{_cell(analysis.provenance.commit_sha)}</code>, clean worktree)'}</p>
  {_summary("Changed Lines", analysis.metrics.lines)}
  {_line_evidence(analysis.metrics.lines, analysis.metrics.line_evidence)}
  {_summary("Changed Branches", analysis.metrics.branches)}
  <section><h2>Line Findings</h2><table><thead><tr><th>Path</th><th>Line</th><th>Status</th><th>Hits</th><th>Reason</th></tr></thead><tbody>{line_rows}</tbody></table></section>
  <section><h2>Excluded Lines</h2><table><thead><tr><th>Path</th><th>Line</th><th>Reason</th></tr></thead><tbody>{excluded_rows}</tbody></table></section>
  <section><h2>Branch Findings</h2><table><thead><tr><th>Path</th><th>Line</th><th>Covered / Total</th><th>Reason</th></tr></thead><tbody>{branch_rows}</tbody></table></section>
  <section><h2>Supporting Evidence</h2>{evidence}</section>
</body>
</html>
"""
