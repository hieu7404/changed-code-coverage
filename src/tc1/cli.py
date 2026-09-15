"""CLI with WP3 Git change acquisition; coverage analysis follows in WP4-WP9."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tc1 import __version__
from tc1.errors import AnalysisNotImplementedError, TC1Error
from tc1.models import AnalysisRequest
from tc1.git_diff import read_git_diff


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tc1",
        description="Changed-Code Coverage Analyzer (WP3 Git diff).",
        allow_abbrev=False,
    )
    parser.add_argument("--version", action="version", version=f"tc1 {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser(
        "analyze",
        help="read Git changes (coverage analysis not implemented yet)",
        description="WP3 reads Git changes; coverage analysis and reports are not yet available.",
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
    """Resolve changed code, then explicitly stop before unavailable coverage stages."""
    changes = read_git_diff(request.repo, request.base, request.head)
    raise AnalysisNotImplementedError(
        "coverage analysis and reports are not implemented yet (WP4-WP9); "
        f"Git diff resolved {len(changes.files)} changed files."
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
