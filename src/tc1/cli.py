"""Acquire, map, summarize and render changed-code coverage reports."""

import argparse
import os
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from tc1 import __version__
from tc1.cobertura import read_cobertura
from tc1.errors import InputError, ReportWriteError, TC1Error
from tc1.git_diff import read_git_diff
from tc1.matcher import map_changed_code
from tc1.metrics import attach_metrics
from tc1.models import AnalysisRequest, AnalysisResult
from tc1.provenance import verify_provenance
from tc1.report_html import render_html
from tc1.report_json import render_json
from tc1.report_markdown import render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tc1",
        description="Changed-Code Coverage Analyzer.",
        allow_abbrev=False,
    )
    parser.add_argument("--version", action="version", version=f"tc1 {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser(
        "analyze",
        help="analyze changed code and write requested reports",
        description="Map changed code to Cobertura evidence and write requested reports.",
        allow_abbrev=False,
    )
    analyze.add_argument("--repo", type=Path, default=Path("."), help="Git repository (default: .)")
    analyze.add_argument("--base", required=True, help="base Git revision")
    analyze.add_argument("--head", default="HEAD", help="head Git revision (default: HEAD)")
    analyze.add_argument("--coverage", type=Path, required=True, help="Cobertura XML input (relative to current working directory)")
    analyze.add_argument("--json", type=Path, dest="json_output", help="JSON report destination")
    analyze.add_argument("--markdown", type=Path, dest="markdown_output", help="Markdown report destination")
    analyze.add_argument("--html", type=Path, dest="html_output", help="HTML report destination")
    analyze.add_argument(
        "--report-generator-html", type=Path,
        help="optional ReportGenerator HTML entry point to link as supporting evidence",
    )
    analyze.add_argument(
        "--exclude-path", action="append", default=[], metavar="PATTERN",
        help="exclude changed lines matching a repository-relative path glob (repeatable)",
    )
    analyze.add_argument(
        "--provenance", type=Path,
        help="strict JSON sidecar describing the Cobertura collection input",
    )
    analyze.add_argument(
        "--require-provenance", action="store_true",
        help="fail unless --provenance is supplied and verifies the selected head and coverage XML",
    )
    return parser


def _report_generator_link(output: Path, evidence: Path | None) -> tuple[str | None, bool]:
    """Return an output-relative, portable evidence link and its availability."""
    if evidence is None:
        return None, False
    resolved_output = output.resolve()
    resolved_evidence = evidence.resolve()
    try:
        link = os.path.relpath(resolved_evidence, start=resolved_output.parent)
    except ValueError:
        # Windows cannot make a relative link between drives. Preserve the requested
        # path rather than silently selecting a different evidence location.
        link = str(resolved_evidence)
    return Path(link).as_posix(), resolved_evidence.is_file()


def _requested_reports(
    request: AnalysisRequest, analysis: AnalysisResult,
) -> tuple[tuple[Path, str], ...]:
    """Render every requested artifact before writing any destination."""
    report_specs = (
        (request.json_output, render_json),
        (request.markdown_output, render_markdown),
        (request.html_output, render_html),
    )
    destinations = [path for path, _ in report_specs if path is not None]
    resolved = [path.resolve() for path in destinations]
    if len(set(resolved)) != len(resolved):
        raise InputError("report destinations must be distinct")

    reports = []
    for path, renderer in report_specs:
        if path is None:
            continue
        evidence_link, evidence_available = _report_generator_link(path, request.report_generator_html)
        reports.append((path, renderer(
            analysis,
            report_generator_html=evidence_link,
            report_generator_available=evidence_available,
        )))
    return tuple(reports)


def _write_reports(reports: tuple[tuple[Path, str], ...]) -> None:
    for destination, content in reports:
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise ReportWriteError(f"cannot write report {destination}: {exc.strerror or exc}") from exc


def analyze(request: AnalysisRequest) -> None:
    """Read, map, summarize and write every report explicitly requested."""
    changes = read_git_diff(request.repo, request.base, request.head)
    provenance = verify_provenance(
        request.provenance, request.coverage, changes.head_commit, required=request.require_provenance,
    )
    coverage = read_cobertura(request.coverage)
    analysis = attach_metrics(replace(
        map_changed_code(changes, coverage, request.exclude_paths), provenance=provenance,
    ))
    _write_reports(_requested_reports(request, analysis))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    request = AnalysisRequest(
        repo=args.repo,
        base=args.base,
        head=args.head,
        coverage=args.coverage,
        json_output=args.json_output,
        markdown_output=args.markdown_output,
        html_output=args.html_output,
        report_generator_html=args.report_generator_html,
        exclude_paths=tuple(args.exclude_path),
        provenance=args.provenance,
        require_provenance=args.require_provenance,
    )
    try:
        analyze(request)
    except TC1Error as exc:
        print(f"tc1: error: {exc}", file=sys.stderr)
        return 1
    return 0
