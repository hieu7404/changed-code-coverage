"""Validate the opt-in, conservative executable-candidate prototype."""

import json

from tc1 import cli
from tc1.candidate_model import classify_csharp_source


def _coverage() -> str:
    return """<coverage><packages><package><classes>
<class filename="src/Service.cs"><lines>
  <line number="4" hits="3" />
  <line number="9" hits="2" />
</lines></class>
</classes></package></packages></coverage>"""


def test_classifier_keeps_executable_statements_and_marks_audited_source_forms():
    source = """namespace Sample;

public class Service
{
    // comment
    public void Run(
        string input)
    {
        const string Label = \"label\";
        try
        {
            value++;
        }
    }
}
"""
    forms = classify_csharp_source(source)
    assert forms == (
        "using_or_namespace", "blank", "type_declaration", "brace", "comment",
        "declaration_or_signature", "declaration_or_signature", "brace",
        "const_declaration", "control_flow_label", "brace", None, "brace", "brace", "brace",
    )


def test_classifier_marks_multiline_raw_string_content_only():
    forms = classify_csharp_source("""private const string Usage = \"\"\"
line one
line two
\"\"\";
""")
    assert forms == ("const_declaration", "raw_string_literal", "raw_string_literal", "raw_string_literal")


def test_executable_prototype_is_opt_in_and_preserves_explicit_evidence(git_repo, tmp_path):
    base = git_repo.commit()
    git_repo.write("src/Service.cs", """namespace Sample;

public class Service
{
    // comment
    public void Run(
        string input)
    {
        var executed = input.Length;
        _ = executed;
    }
}
""")
    git_repo.commit()
    coverage = tmp_path / "coverage.xml"
    coverage.write_text(_coverage(), encoding="utf-8")
    default_output = tmp_path / "default.json"
    prototype_output = tmp_path / "prototype.json"

    assert cli.main([
        "analyze", "--repo", str(git_repo.path), "--base", base,
        "--coverage", str(coverage), "--json", str(default_output),
    ]) == 0
    assert cli.main([
        "analyze", "--repo", str(git_repo.path), "--base", base,
        "--coverage", str(coverage), "--candidate-model", "executable_prototype",
        "--json", str(prototype_output),
    ]) == 0

    default = json.loads(default_output.read_text(encoding="utf-8"))
    prototype = json.loads(prototype_output.read_text(encoding="utf-8"))
    assert default["analysis"]["candidate_model"] == "all_changed_lines"
    assert default["metrics"]["lines"] == {
        "candidates": 12, "classifiable": 2, "covered": 2, "uncovered": 0,
        "unknown": 10, "excluded": 0, "coverage_percent": 100.0,
    }
    assert prototype["analysis"]["candidate_model"] == "executable_prototype"
    assert prototype["metrics"]["lines"] == {
        "candidates": 12, "classifiable": 2, "covered": 2, "uncovered": 0,
        "unknown": 1, "excluded": 9, "coverage_percent": 100.0,
    }
    assert prototype["metrics"]["line_evidence"] == {
        "in_scope": 3, "classifiable": 2, "classifiable_rate": 100 * 2 / 3,
        "unknown_rate": 100 / 3,
    }
    assert [(line["line"], line["status"]) for line in prototype["lines"]] == [
        (4, "covered"), (9, "covered"), (10, "unknown"),
    ]
    assert prototype["lines"][-1]["reason"] == "no_explicit_line_evidence"
    assert {item["reason"] for item in prototype["excluded_lines"]} == {
        "candidate_model:executable_prototype:using_or_namespace",
        "candidate_model:executable_prototype:blank",
        "candidate_model:executable_prototype:type_declaration",
        "candidate_model:executable_prototype:comment",
        "candidate_model:executable_prototype:declaration_or_signature",
        "candidate_model:executable_prototype:brace",
    }
