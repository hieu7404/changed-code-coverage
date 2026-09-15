"""WP2 CLI contract; analysis is implemented in later work packages."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tc1 import __version__
from tc1.errors import AnalysisNotImplementedError, TC1Error
from tc1.models import AnalysisRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tc1",
        description="Changed-Code Coverage Analyzer (WP2 bootstrap).",
        allow_abbrev=False,
    )
    parser.add_argument("--version", action="version", version=f"tc1 {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser(
        "analyze",
        help="accept analysis arguments (pipeline not implemented yet)",
        description="WP2 accepts arguments only; analysis and reports are not yet available.",
        allow_abbrev=False,
    )
    analyze.add_argument("--repo", type=Path, default=Path("."), help="Git repository (default: .)")
    analyze.add_argument("--base", required=True, help="base Git revision")
    analyze.add_argument("--head", default="HEAD", help="head Git revision (default: HEAD)")
    analyze.add_argument("--coverage", type=Path, required=True, help="Cobertura XML input")
    analyze.add_argument("--json", type=Path, dest="json_output", help="JSON report destination")
    analyze.add_argument("--markdown", type=Path, dest="markdown_output", help="Markdown report destination")
    analyze.add_argument("--html", type=Path, dest="html_output", help="HTML report destination")
    return parser


def analyze(request: AnalysisRequest) -> None:
    """Reserved pipeline boundary; never fabricate a successful empty report."""
    raise AnalysisNotImplementedError(
        "analysis is not implemented yet (WP2 bootstrap); "
        "Git diff, coverage mapping, metrics and reports follow in WP3-WP9."
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
