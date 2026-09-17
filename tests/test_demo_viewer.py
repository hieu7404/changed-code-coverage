"""Structural checks for the dependency-free static demo viewer."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"

def _embedded_data(script_id: str) -> dict[str, object]:
    page = (DEMO / "index.html").read_text(encoding="utf-8")
    match = re.search(rf'<script id="{script_id}" type="application/json">\s*(.*?)\s*</script>', page, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))

def test_demo_viewer_has_one_report_flow_and_local_assets() -> None:
    page = (DEMO / "index.html").read_text(encoding="utf-8")
    assert "Open report.json" in page
    assert "Show sample report" in page
    assert "Load live report" not in page
    assert "Evaluation summary" not in page
    assert "styles.css" in page
    assert "app.js" in page
    assert (DEMO / "styles.css").is_file()
    assert (DEMO / "app.js").is_file()

def test_showcase_report_exercises_visible_tc1_evidence_states() -> None:
    report = _embedded_data("showcase-report")
    assert report["schema_version"] == "1.0"
    assert report["metrics"]["lines"]["coverage_percent"] == 50.0
    assert {finding["status"] for finding in report["lines"]} == {"covered", "uncovered", "unknown"}
    assert len(report["excluded_lines"]) == 2
    assert report["metrics"]["branches"]["coverage_percent"] == 75.0

def test_demo_viewer_uses_safe_dom_text_and_supports_report_urls() -> None:
    application = (DEMO / "app.js").read_text(encoding="utf-8")
    assert "textContent" in application
    assert "innerHTML" not in application
    assert "URLSearchParams" in application
    assert "fetch(url)" in application
    assert 'query.get("report")' in application
