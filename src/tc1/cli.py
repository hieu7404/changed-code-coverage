"""Acquire, path-normalize and line-map inputs; later stages follow in WP7-WP9."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tc1 import __version__
from tc1.cobertura import read_cobertura
from tc1.errors import AnalysisNotImplementedError, TC1Error
from tc1.git_diff import read_git_diff
from tc1.matcher import map_changed_lines
from tc1.models import AnalysisRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tc1",
        description="Changed-Code Coverage Analyzer (WP6 line mapping).",
        allow_abbrev=False,
    )
    parser.add_argument("--version", action="version", version=f"tc1 {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser(
        "analyze",
        help="read Git and Cobertura inputs (later stages are not yet available)",
        description="WP6 maps changed lines; branch mapping, metrics and reports are not yet available.",
        allow_abbrev=False,
    )
    analyze.add_argument("--repo", type=Path, default=Path("."), help="Git repository (default: .)")
    analyze.add_argument("--base", required=True, help="base Git revision")
    analyze.add_argument("--head", default="HEAD", help="head Git revision (default: HEAD)")
    analyze.add_argument("--coverage", type=Path, required=True, help="Cobertura XML input (relative to current working directory)")
    analyze.add_argument("--json", type=Path, dest="json_output", help="JSON report destination")
    analyze.add_argument("--markdown", type=Path, dest="markdown_output", help="Markdown report destination")
    analyze.add_argument("--html", type=Path, dest="html_output", help="HTML report destination")
    return parser


def analyze(request: AnalysisRequest) -> None:
    """Read, path-normalize and line-map inputs, then stop before WP7-WP9."""
    changes = read_git_diff(request.repo, request.base, request.head)
    coverage = read_cobertura(request.coverage)
    analysis = map_changed_lines(changes, coverage)
    raise AnalysisNotImplementedError(
        "branch mapping, metrics and reports are not implemented yet (WP7-WP9); "
        f"Git diff resolved {len(changes.files)} changed files; "
        f"Cobertura parsed {len(coverage.line_entries)} class-level line entries; "
        f"line mapper produced {len(analysis.lines)} changed-line results."
    )


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
    )
    try:
        analyze(request)
    except TC1Error as exc:
        print(f"tc1: error: {exc}", file=sys.stderr)
        return 1
    return 0