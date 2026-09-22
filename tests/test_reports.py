"""Validate deterministic JSON, Markdown and HTML report renderers."""

import json

import pytest

from tc1.errors import ModelValidationError
from tc1.metrics import attach_metrics
from tc1.models import (
    AnalysisResult,
    BranchAggregate,
    BranchResult,
    CoverageStatus,
    ExcludedLine,
    LineResult,
    SourceLocation,
)
from tc1.report_html import render_html
from tc1.report_json import analysis_data, render_json
from tc1.report_markdown import render_markdown


def _location(line: int) -> SourceLocation:
    return SourceLocation("src/Service|Name.cs", line)


def _analysis() -> AnalysisResult:
    return attach_metrics(AnalysisResult(
        "base<rev>", "head&rev",
        lines=(
            LineResult(_location(1), CoverageStatus.COVERED, "positive <hits>", 3),
            LineResult(_location(2), CoverageStatus.UNCOVERED, "zero hits", 0),
            LineResult(_location(3), CoverageStatus.UNKNOWN, "missing|evidence"),
        ),
        excluded_lines=(ExcludedLine(_location(4), "generated\nsource"),),
        branches=(
            BranchResult(_location(5), "partial aggregate", BranchAggregate(1, 2)),
            BranchResult(_location(6), "ambiguous metadata"),
        ),
    ))


def test_renderers_share_the_attached_metrics_and_keep_unknown_visible():
    analysis = _analysis()
    data = analysis_data(analysis, report_generator_html="coverage/index.html", report_generator_available=True)
    markdown = render_markdown(analysis, report_generator_html="coverage/index.html", report_generator_available=True)
    html = render_html(analysis, report_generator_html="coverage/index.html", report_generator_available=True)

    assert data["metrics"] == {
        "lines": {
            "candidates": 4, "classifiable": 2, "covered": 1, "uncovered": 1,
            "unknown": 1, "excluded": 1, "coverage_percent": 50.0,
        },
        "branches": {
            "candidates": 3, "classifiable": 2, "covered": 1, "uncovered": 1,
            "unknown": 1, "excluded": 0, "coverage_percent": 50.0,
        },
        "line_evidence": {
            "in_scope": 3, "classifiable": 2, "classifiable_rate": 100 * 2 / 3,
            "unknown_rate": 100 / 3,
        },
    }
    assert "| 4 | 2 | 1 | 1 | 1 | 1 | 50.00% |" in markdown
    assert "**Changed-code coverage:** 50.00%." in markdown
    assert "**Evidence available for:** 66.67% of in-scope changed lines (2 / 3)." in markdown
    assert "**Unknown evidence:** 33.33% of in-scope changed lines." in markdown
    assert "| 3 | 2 | 1 | 1 | 1 | 0 | 50.00% |" in markdown
    assert ">50.00%</td>" in html
    assert "Evidence available for:</strong> 66.67% of in-scope changed lines (2 / 3)." in html
    assert "Unknown evidence:</strong> 33.33% of in-scope changed lines." in html
    assert markdown.endswith("\n")
    assert html.startswith("<!doctype html>")


def test_json_schema_retains_evidence_and_is_deterministic():
    rendered = render_json(_analysis(), report_generator_html="coverage/index.html", report_generator_available=True)
    data = json.loads(rendered)

    assert rendered.endswith("\n")
    assert data["schema_version"] == "1.3"
    assert data["analysis"] == {
        "base": "base<rev>", "head": "head&rev", "candidate_model": "all_changed_lines",
    }
    assert data["provenance"] == {"status": "unverified"}
    assert data["lines"][0] == {
        "path": "src/Service|Name.cs", "line": 1, "status": "covered",
        "reason": "positive <hits>", "hits": 3,
    }
    assert data["branches"] == [
        {
            "path": "src/Service|Name.cs", "line": 5, "reason": "partial aggregate",
            "aggregate": {"covered": 1, "total": 2, "uncovered": 1},
        },
        {
            "path": "src/Service|Name.cs", "line": 6, "reason": "ambiguous metadata",
            "aggregate": None,
        },
    ]


def test_text_renderers_escape_evidence_while_markdown_preserves_readability():
    analysis = _analysis()

    markdown = render_markdown(analysis)
    html = render_html(analysis, report_generator_html='coverage/"unsafe".html', report_generator_available=True)

    assert "src/Service\\|Name.cs" in markdown
    assert "missing\\|evidence" in markdown
    assert "generated<br>source" in markdown
    assert "base&lt;rev&gt;" in html
    assert "head&amp;rev" in html
    assert "Coverage provenance: <strong>unverified</strong>" in html
    assert "Candidate model: <code>all_changed_lines</code>" in html
    assert "positive &lt;hits&gt;" in html
    assert 'href="coverage/&quot;unsafe&quot;.html"' in html


@pytest.mark.parametrize("renderer", [analysis_data, render_json, render_markdown, render_html])
def test_renderers_require_precomputed_metrics(renderer):
    with pytest.raises(ModelValidationError, match="reports require AnalysisResult.metrics"):
        renderer(AnalysisResult("base", "head"))


def test_renderers_show_not_applicable_for_zero_denominator():
    analysis = attach_metrics(AnalysisResult(
        "base", "head",
        lines=(LineResult(_location(1), CoverageStatus.UNKNOWN, "missing evidence"),),
        branches=(BranchResult(_location(2), "ambiguous metadata"),),
    ))

    assert json.loads(render_json(analysis))["metrics"]["lines"]["coverage_percent"] is None
    assert json.loads(render_json(analysis))["metrics"]["line_evidence"] == {
        "in_scope": 1, "classifiable": 0, "classifiable_rate": 0.0, "unknown_rate": 100.0,
    }
    assert "N/A" in render_markdown(analysis)
    assert ">N/A</td>" in render_html(analysis)
