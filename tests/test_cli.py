"""Exercise the installed CLI and its report/output contract."""

import json
import hashlib
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

from tc1 import __version__, cli
from tc1.errors import InputError, ModelValidationError
from tc1.models import AnalysisRequest, CandidateModel


def test_module_help_outside_repository(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "tc1", "--help"],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    assert "analyze" in result.stdout
    assert result.stderr == ""


def test_installed_console_script_version(tmp_path):
    scripts = Path(sysconfig.get_path("scripts"))
    executable = scripts / ("tc1.exe" if sys.platform == "win32" else "tc1")
    result = subprocess.run(
        [str(executable), "--version"],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == f"tc1 {__version__}"
    assert result.stderr == ""


def test_analyze_help_explains_reports(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["analyze", "--help"])
    assert exc.value.code == 0
    assert "write requested reports" in capsys.readouterr().out


@pytest.mark.parametrize("args", [
    [], ["invalid"], ["analyze"], ["analyze", "--base", "main"],
    ["analyze", "--coverage", "coverage.xml"],
    ["analyze", "--base", "main", "--coverage", "coverage.xml", "--threshold", "80"],
    ["analyze", "--base", "main", "--cov", "coverage.xml"],
])
def test_invalid_usage_exits_two(args, capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(args)
    assert exc.value.code == 2
    assert "error:" in capsys.readouterr().err


def test_arguments_reach_pipeline_without_path_guessing(monkeypatch):
    received = []
    monkeypatch.setattr(cli, "analyze", received.append)
    assert cli.main([
        "analyze", "--repo", "repo with spaces", "--base", "feature~1", "--head", "feature",
        "--coverage", "input/coverage.xml", "--json", "output/report.json",
        "--markdown", "output/report.md", "--html", "output/index.html",
        "--report-generator-html", "output/coverage/index.html",
        "--exclude-path", "**/*.g.cs", "--exclude-path", "vendor/**",
        "--candidate-model", "executable_prototype",
        "--provenance", "input/coverage-run.json", "--require-provenance",
    ]) == 0
    assert received == [AnalysisRequest(
        repo=Path("repo with spaces"), base="feature~1", head="feature",
        coverage=Path("input/coverage.xml"), json_output=Path("output/report.json"),
        markdown_output=Path("output/report.md"), html_output=Path("output/index.html"),
        report_generator_html=Path("output/coverage/index.html"),
        exclude_paths=("**/*.g.cs", "vendor/**"),
        provenance=Path("input/coverage-run.json"), require_provenance=True,
        candidate_model=CandidateModel.EXECUTABLE_PROTOTYPE,
    )]


def test_argument_defaults(monkeypatch):
    received = []
    monkeypatch.setattr(cli, "analyze", received.append)
    assert cli.main(["analyze", "--base", "main", "--coverage", "coverage.xml"]) == 0
    assert received == [AnalysisRequest(Path("."), "main", "HEAD", Path("coverage.xml"))]


def test_analyze_writes_requested_reports_and_links_supporting_evidence(git_repo, tmp_path, capsys):
    git_repo.commit()
    output = tmp_path / "output"
    output.mkdir()
    coverage = output / "coverage.xml"
    coverage.write_text("<coverage><packages/></coverage>", encoding="utf-8")
    evidence = output / "coverage" / "index.html"
    evidence.parent.mkdir()
    evidence.write_text("<html>ReportGenerator</html>", encoding="utf-8")

    assert cli.main([
        "analyze", "--repo", str(git_repo.path), "--base", "HEAD", "--coverage", str(coverage),
        "--json", str(output / "report.json"), "--markdown", str(output / "report.md"),
        "--html", str(output / "index.html"), "--report-generator-html", str(evidence),
    ]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["metrics"]["lines"] == {
        "candidates": 0, "classifiable": 0, "covered": 0, "uncovered": 0,
        "unknown": 0, "excluded": 0, "coverage_percent": None,
    }
    assert report["metrics"]["line_evidence"] == {
        "in_scope": 0, "classifiable": 0, "classifiable_rate": None, "unknown_rate": None,
    }
    assert report["supporting_evidence"] == {
        "report_generator_html": "coverage/index.html", "available": True,
    }
    assert "[Open ReportGenerator coverage HTML](coverage/index.html)" in (output / "report.md").read_text(encoding="utf-8")
    assert 'href="coverage/index.html"' in (output / "index.html").read_text(encoding="utf-8")


def test_analyze_reports_missing_supporting_evidence_without_fabricating_a_link(git_repo, tmp_path):
    git_repo.commit()
    coverage = tmp_path / "coverage.xml"
    coverage.write_text("<coverage><packages/></coverage>", encoding="utf-8")
    output = tmp_path / "report.json"
    missing = tmp_path / "coverage" / "index.html"

    assert cli.main([
        "analyze", "--repo", str(git_repo.path), "--base", "HEAD", "--coverage", str(coverage),
        "--json", str(output), "--report-generator-html", str(missing),
    ]) == 0
    evidence = json.loads(output.read_text(encoding="utf-8"))["supporting_evidence"]
    assert evidence == {"report_generator_html": "coverage/index.html", "available": False}


def test_analyze_verifies_provenance_before_writing_reports(git_repo, tmp_path, capsys):
    head = git_repo.commit()
    coverage = tmp_path / "coverage.xml"
    coverage.write_text("<coverage><packages/></coverage>", encoding="utf-8")
    provenance = tmp_path / "coverage-run.json"
    provenance.write_text(json.dumps({
        "schema_version": "1.0", "commit_sha": head, "dirty_state": False,
        "collector": "coverlet.collector", "collector_version": "6.0.4",
        "collection_command": "dotnet test", "target_framework": "net10.0",
        "coverage_xml_sha256": hashlib.sha256(coverage.read_bytes()).hexdigest(),
        "timestamp": "2026-09-22T00:00:00Z",
    }), encoding="utf-8")
    output = tmp_path / "report.json"

    assert cli.main([
        "analyze", "--repo", str(git_repo.path), "--base", "HEAD", "--coverage", str(coverage),
        "--provenance", str(provenance), "--require-provenance", "--json", str(output),
    ]) == 0
    assert capsys.readouterr().err == ""
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["provenance"] == {
        "status": "verified", "commit_sha": head, "dirty_state": False,
        "collector": "coverlet.collector", "collector_version": "6.0.4",
        "collection_command": "dotnet test", "target_framework": "net10.0",
        "coverage_xml_sha256": hashlib.sha256(coverage.read_bytes()).hexdigest(),
        "timestamp": "2026-09-22T00:00:00Z",
    }


def test_analyze_fails_on_provenance_mismatch_without_writing_reports(git_repo, tmp_path, capsys):
    git_repo.commit()
    coverage = tmp_path / "coverage.xml"
    coverage.write_text("<coverage><packages/></coverage>", encoding="utf-8")
    provenance = tmp_path / "coverage-run.json"
    provenance.write_text(json.dumps({
        "schema_version": "1.0", "commit_sha": "a" * 40, "dirty_state": False,
        "collector": "coverlet.collector", "collector_version": "6.0.4",
        "collection_command": "dotnet test", "target_framework": "net10.0",
        "coverage_xml_sha256": hashlib.sha256(coverage.read_bytes()).hexdigest(),
        "timestamp": "2026-09-22T00:00:00Z",
    }), encoding="utf-8")
    output = tmp_path / "report.json"
    output.write_text("existing", encoding="utf-8")

    assert cli.main([
        "analyze", "--repo", str(git_repo.path), "--base", "HEAD", "--coverage", str(coverage),
        "--provenance", str(provenance), "--json", str(output),
    ]) == 1
    assert "does not match analysis head" in capsys.readouterr().err
    assert output.read_text(encoding="utf-8") == "existing"


def test_analyze_rejects_colliding_report_destinations_before_writing(git_repo, tmp_path, capsys):
    git_repo.commit()
    coverage = tmp_path / "coverage.xml"
    coverage.write_text("<coverage><packages/></coverage>", encoding="utf-8")
    output = tmp_path / "report"
    output.write_text("existing", encoding="utf-8")

    assert cli.main([
        "analyze", "--repo", str(git_repo.path), "--base", "HEAD", "--coverage", str(coverage),
        "--json", str(output), "--markdown", str(output),
    ]) == 1
    assert capsys.readouterr().err == "tc1: error: report destinations must be distinct\n"
    assert output.read_text(encoding="utf-8") == "existing"


@pytest.mark.parametrize("error", [InputError, ModelValidationError])
def test_expected_errors_are_presented_without_traceback(error, monkeypatch, capsys):
    def fail(request):
        raise error("invalid evidence")

    monkeypatch.setattr(cli, "analyze", fail)
    assert cli.main(["analyze", "--base", "main", "--coverage", "coverage.xml"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "tc1: error: invalid evidence\n"


def test_programming_errors_are_not_hidden(monkeypatch):
    def fail(request):
        raise RuntimeError("implementation defect")

    monkeypatch.setattr(cli, "analyze", fail)
    with pytest.raises(RuntimeError, match="implementation defect"):
        cli.main(["analyze", "--base", "main", "--coverage", "coverage.xml"])


def test_analyze_reports_git_input_errors(git_repo, capsys):
    git_repo.commit()
    assert cli.main([
        "analyze", "--repo", str(git_repo.path), "--base", "missing", "--coverage", "unused.xml",
    ]) == 1
    error = capsys.readouterr().err
    assert "Git rev-parse failed" in error
    assert "Traceback" not in error


@pytest.mark.parametrize("data", [
    None, "<broken", "<wrong-root/>",
    '<coverage><packages><package><classes><class filename="F.cs"><lines>'
    '<line number="1"/></lines></class></classes></package></packages></coverage>',
])
def test_analyze_reports_cobertura_errors_without_touching_outputs(git_repo, tmp_path, capsys, data):
    git_repo.commit()
    coverage = tmp_path / "coverage.xml"
    if data is not None:
        coverage.write_text(data, encoding="utf-8")
    output = tmp_path / "report.json"
    output.write_text("existing", encoding="utf-8")
    assert cli.main([
        "analyze", "--repo", str(git_repo.path), "--base", "HEAD",
        "--coverage", str(coverage), "--json", str(output),
    ]) == 1
    error = capsys.readouterr().err
    assert "Cobertura" in error
    assert "coverage.xml" in error
    assert "Traceback" not in error
    assert output.read_text(encoding="utf-8") == "existing"


def test_analyze_accepts_canonical_cobertura_entries_without_report_destinations(git_repo, capsys):
    git_repo.commit()
    coverage = Path(__file__).resolve().parents[1] / "fixtures/cobertura/coverlet_sample.xml"
    assert cli.main([
        "analyze", "--repo", str(git_repo.path), "--base", "HEAD", "--coverage", str(coverage),
    ]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_analyze_writes_explicit_path_exclusions(git_repo, tmp_path):
    base = git_repo.commit()
    git_repo.write("src/Generated.g.cs", "first\nsecond\n")
    git_repo.commit()
    coverage = tmp_path / "coverage.xml"
    coverage.write_text("<coverage><packages/></coverage>", encoding="utf-8")
    output = tmp_path / "report.json"

    assert cli.main([
        "analyze", "--repo", str(git_repo.path), "--base", base,
        "--coverage", str(coverage), "--json", str(output),
        "--exclude-path", "**/*.g.cs",
    ]) == 0

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["lines"] == []
    assert report["branches"] == []
    assert report["metrics"]["lines"] == {
        "candidates": 2, "classifiable": 0, "covered": 0, "uncovered": 0,
        "unknown": 0, "excluded": 2, "coverage_percent": None,
    }
    assert report["metrics"]["line_evidence"] == {
        "in_scope": 0, "classifiable": 0, "classifiable_rate": None, "unknown_rate": None,
    }
    assert report["excluded_lines"] == [
        {"path": "src/Generated.g.cs", "line": 1, "reason": "path_rule:**/*.g.cs"},
        {"path": "src/Generated.g.cs", "line": 2, "reason": "path_rule:**/*.g.cs"},
    ]
