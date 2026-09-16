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
    assert "WP6 maps changed lines" in capsys.readouterr().out


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
    (output.parent / "coverage.xml").write_text("<coverage><packages/></coverage>", encoding="utf-8")
    git_repo.write("coverage.xml", "<wrong-root/>")
    result = subprocess.run(
        [sys.executable, "-m", "tc1", "analyze", "--repo", str(git_repo.path), "--base", "HEAD",
         "--coverage", "coverage.xml", "--json", str(output),
         "--markdown", "report.md", "--html", "index.html"],
        cwd=output.parent, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "branch mapping, metrics and reports are not implemented yet" in result.stderr
    assert "Cobertura parsed 0 class-level line entries" in result.stderr
    assert "Git diff resolved 0 changed files" in result.stderr
    assert "Traceback" not in result.stderr
    assert output.read_text(encoding="utf-8") == "existing evidence"
    assert sorted(path.name for path in output.parent.iterdir()) == ["coverage.xml", "report.json"]


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
    assert "not implemented" not in error
    assert "Traceback" not in error
    assert output.read_text(encoding="utf-8") == "existing"


def test_analyze_reads_canonical_cobertura_entries_before_stopping(git_repo, capsys):
    git_repo.commit()
    coverage = Path(__file__).resolve().parents[1] / "fixtures/cobertura/coverlet_sample.xml"
    assert cli.main([
        "analyze", "--repo", str(git_repo.path), "--base", "HEAD",
        "--coverage", str(coverage),
    ]) == 1
    error = capsys.readouterr().err
    assert "Git diff resolved 0 changed files" in error
    assert "Cobertura parsed 12 class-level line entries" in error
    assert "WP7-WP9" in error
    assert "line mapper produced 0 changed-line results" in error
