"""Exercise the installed CLI and its failure/output contract."""

import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

from tc1 import __version__, cli
from tc1.errors import InputError, ModelValidationError
from tc1.models import AnalysisRequest


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


def test_analyze_help_explains_bootstrap(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["analyze", "--help"])
    assert exc.value.code == 0
    assert "not yet available" in capsys.readouterr().out


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
    ]) == 0
    assert received == [AnalysisRequest(
        repo=Path("repo with spaces"), base="feature~1", head="feature",
        coverage=Path("input/coverage.xml"), json_output=Path("output/report.json"),
        markdown_output=Path("output/report.md"), html_output=Path("output/index.html"),
    )]


def test_argument_defaults(monkeypatch):
    received = []
    monkeypatch.setattr(cli, "analyze", received.append)
    assert cli.main(["analyze", "--base", "main", "--coverage", "coverage.xml"]) == 0
    assert received == [AnalysisRequest(Path("."), "main", "HEAD", Path("coverage.xml"))]


def test_unimplemented_analysis_preserves_existing_output(tmp_path, git_repo):
    git_repo.commit()
    output = tmp_path / "output" / "report.json"
    output.parent.mkdir()
    output.write_text("existing evidence", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "tc1", "analyze", "--repo", str(git_repo.path), "--base", "HEAD",
         "--coverage", "missing.xml", "--json", str(output),
         "--markdown", "report.md", "--html", "index.html"],
        cwd=output.parent, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "coverage analysis and reports are not implemented yet" in result.stderr
    assert "Git diff resolved 0 changed files" in result.stderr
    assert "Traceback" not in result.stderr
    assert output.read_text(encoding="utf-8") == "existing evidence"
    assert sorted(path.name for path in output.parent.iterdir()) == ["report.json"]


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
    assert cli.main(["analyze", "--repo", str(git_repo.path), "--base", "missing",
                     "--coverage", "unused.xml"]) == 1
    error = capsys.readouterr().err
    assert "Git rev-parse failed" in error
    assert "not implemented" not in error
    assert "Traceback" not in error
