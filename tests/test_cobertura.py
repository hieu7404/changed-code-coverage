"""Deterministic Cobertura evidence and malformed-input cases."""

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from tc1.cobertura import parse_cobertura, read_cobertura
from tc1.errors import CoberturaError, InputError

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
EXPECTED = json.loads((FIXTURES / "expected/cobertura.json").read_text(encoding="utf-8"))


def document(lines: str, *, filename: str = "F.cs") -> bytes:
    return (
        f'<coverage><packages><package><classes><class filename="{filename}">'
        f'<lines>{lines}</lines></class></classes></package></packages></coverage>'
    ).encode()


def test_reviewed_coverlet_sample_uses_class_lines_once():
    report = read_cobertura(FIXTURES / "cobertura/coverlet_sample.xml")
    assert list(report.sources) == EXPECTED["sources"]
    assert report.packages[0].name == "Tc1.Sample"
    assert len(report.classes) == 1
    source = report.classes[0]
    assert source.filename == EXPECTED["filename"]
    assert source.name == "Tc1.Sample.DiscountService"
    assert source.lines_present is True
    assert [[line.location.line, line.hits] for line in report.line_entries] == EXPECTED["line_hits"]
    assert all(line.location.path == source.filename for line in report.line_entries)
    assert len(source.methods[0].lines) == EXPECTED["method_entry_count"]
    assert source.methods[0].lines == source.lines
    assert source.methods[0].lines_present is True
    assert source.methods[0].signature == "(System.Decimal)"
    assert sum(line.hits > 0 for line in report.line_entries) == EXPECTED["covered_entries"]
    assert sum(line.hits == 0 for line in report.line_entries) == EXPECTED["zero_hit_entries"]
    branch_lines = [
        [line.location.line, line.branch, line.condition_coverage,
         line.conditions[0].number, line.conditions[0].coverage]
        for line in source.lines if line.conditions
    ]
    assert branch_lines == EXPECTED["branch_conditions"]
    assert dict(report.attributes)["line-rate"] == "0.8332999999999999"


def test_duplicates_and_cross_package_paths_are_not_merged():
    report = read_cobertura(FIXTURES / "cobertura/multiple_packages.xml")
    assert report.sources == ("./first/", "../second/")
    assert [package.name for package in report.packages] == ["one", "two"]
    assert [item.name for item in report.classes] == ["A", "Other", "B"]
    shared = [line for line in report.line_entries if line.location.path == "Shared.cs"]
    assert [(line.location.line, line.hits) for line in shared] == [(7, 0), (7, 3), (7, 5)]
    assert shared[1].condition_coverage == "50% (1/2)"


def test_missing_evidence_has_no_method_fallback_or_zero_fill():
    report = read_cobertura(FIXTURES / "cobertura/missing_evidence.xml")
    method_only, empty, gaps = report.classes
    assert report.sources == ("", "  ./source root/  ")
    assert method_only.lines_present is False
    assert method_only.lines == ()
    assert method_only.methods[0].lines[0].hits == 9
    assert empty.lines_present is True
    assert empty.lines == ()
    assert [line.location.line for line in report.line_entries] == [3, 7]
    assert gaps.lines[0].branch is None
    assert gaps.lines[0].condition_coverage is None
    assert gaps.lines[1].branch == "maybe"
    assert gaps.lines[1].condition_coverage == "not measured"
    assert gaps.lines[1].conditions[0].number is None
    assert gaps.lines[1].conditions[0].coverage is None
    assert gaps.lines[1].conditions[1].number == "opaque"


def test_namespace_unicode_paths_and_raw_attributes():
    report = read_cobertura(FIXTURES / "cobertura/namespaced.xml")
    line = report.line_entries[0]
    assert report.sources == (r"src\folder",)
    assert line.location.path == "Đơn hàng & phí.cs"
    assert (line.location.line, line.hits, line.branch) == (2, 0, "true")
    assert dict(line.attributes)["hits"] == "000"
    assert dict(line.attributes)["custom"] == "kept"
    assert dict(line.conditions[0].attributes)["collector-id"] == "kept"


def test_empty_coverage_is_an_empty_inventory_not_a_zero_percent():
    report = read_cobertura(FIXTURES / "cobertura/empty.xml")
    assert report.sources == ()
    assert report.classes == ()
    assert report.line_entries == ()


def test_paths_are_not_normalized_or_resolved():
    path = r"  source\nested\..\File.cs  "
    report = parse_cobertura(document('<line number="1" hits="1" />', filename=path))
    assert report.classes[0].filename == path
    assert report.line_entries[0].location.path == path


def test_conflicting_method_evidence_is_kept_separately():
    xml = document('<line number="1" hits="0" />').replace(
        b"<lines>", b'<methods><method><lines><line number="1" hits="9" /></lines></method></methods><lines>', 1,
    )
    source = parse_cobertura(xml).classes[0]
    assert source.lines[0].hits == 0
    assert source.methods[0].lines[0].hits == 9


def test_attribute_order_does_not_change_parsed_records():
    first = document('<line hits="4" number="1" branch="True" />')
    second = document('<line branch="True" number="1" hits="4" />')
    assert parse_cobertura(first) == parse_cobertura(second)


@pytest.mark.parametrize("encoding", ["utf-8", "utf-16", "iso-8859-1"])
def test_declared_xml_encoding_is_honored(encoding):
    xml = '<?xml version="1.0" encoding="' + encoding + '"?>' + document(
        '<line number="1" hits="2" />', filename="café.cs",
    ).decode()
    report = parse_cobertura(xml.encode(encoding))
    assert report.classes[0].filename == "café.cs"


@pytest.mark.parametrize("line", [
    '<line hits="0" />', '<line number="1" />',
    '<line number="0" hits="0" />', '<line number="-1" hits="0" />',
    '<line number="1.5" hits="0" />', '<line number="true" hits="0" />',
    '<line number="1" hits="-1" />', '<line number="1" hits="1.0" />',
    '<line number="1" hits="NaN" />', '<line number="1" hits="true" />',
    '<line number="1" hits="" />', '<line number="1" hits=" 0 " />',
    '<line number="1" hits="٠" />',
])
def test_invalid_explicit_numeric_evidence_is_an_error(line):
    with pytest.raises(CoberturaError):
        parse_cobertura(document(line))


@pytest.mark.parametrize("xml", [
    b"", b"<coverage>", b"<not-coverage />", b"<coverage />",
    b"<coverage><packages/><packages/></coverage>",
    b"<coverage><sources/><sources/><packages/></coverage>",
    b"<coverage><packages><package/></packages></coverage>",
    b"<coverage><line number='1' hits='0'/><packages/></coverage>",
    b"<coverage><packages><class filename='F.cs'/></packages></coverage>",
    b"<coverage><sources><source><nested/></source></sources><packages/></coverage>",
    b"<coverage>unexpected text<packages/></coverage>",
    b"<coverage><packages/>unexpected tail</coverage>",
    b"<coverage xmlns='urn:test'><packages xmlns=''/></coverage>",
    b"<?xml version='1.0' encoding='no-such-encoding'?><coverage><packages/></coverage>",
])
def test_bad_xml_or_unsupported_structure_is_an_error(xml):
    with pytest.raises(CoberturaError):
        parse_cobertura(xml)


@pytest.mark.parametrize("body", [
    '<class><lines/></class>',
    '<class filename=" "><lines/></class>',
    '<class filename="F.cs"><lines/><lines/></class>',
    '<class filename="F.cs"><methods/><methods/></class>',
    '<class filename="F.cs"><line number="1" hits="0"/></class>',
    '<class filename="F.cs"><lines><unknown/></lines></class>',
    '<class filename="F.cs"><lines><line number="1" hits="0"><conditions/><conditions/></line></lines></class>',
    '<class filename="F.cs"><methods><method><lines><line number="1"/></lines></method></methods></class>',
    '<class filename="F.cs"><lines><line number="1" hits="0"><conditions><condition><extra/></condition></conditions></line></lines></class>',
])
def test_invalid_class_structure_does_not_silently_drop_evidence(body):
    xml = f"<coverage><packages><package><classes>{body}</classes></package></packages></coverage>"
    with pytest.raises(CoberturaError):
        parse_cobertura(xml.encode())


@pytest.mark.parametrize("declaration", [
    '<!DOCTYPE coverage SYSTEM "https://example.invalid/coverage.dtd">',
    '<!DOCTYPE coverage [<!ENTITY hits "0">]>',
])
@pytest.mark.parametrize("encoding", ["utf-8", "utf-16"])
def test_dtd_profiles_are_explicitly_rejected(declaration, encoding):
    xml = f'<?xml version="1.0" encoding="{encoding}"?>{declaration}<coverage><packages/></coverage>'
    with pytest.raises(CoberturaError, match="DOCTYPE"):
        parse_cobertura(xml.encode(encoding))


def test_input_file_remains_unchanged(tmp_path):
    path = tmp_path / "coverage.xml"
    data = document('<line number="1" hits="0" />')
    path.write_bytes(data)
    assert read_cobertura(path).line_entries[0].hits == 0
    assert path.read_bytes() == data


@pytest.mark.parametrize("kind", ["missing", "directory", "malformed"])
def test_file_failures_include_input_context(tmp_path, kind):
    path = tmp_path / "coverage.xml"
    if kind == "directory":
        path.mkdir()
    elif kind == "malformed":
        path.write_bytes(b"<broken")
    with pytest.raises(InputError, match="coverage.xml"):
        read_cobertura(path)


def test_unreadable_file_becomes_expected_error(tmp_path, monkeypatch):
    def fail(self):
        raise PermissionError("fixture denied")

    monkeypatch.setattr(Path, "read_bytes", fail)
    with pytest.raises(CoberturaError, match="cannot read Cobertura file"):
        read_cobertura(tmp_path / "coverage.xml")


def test_records_are_frozen():
    report = parse_cobertura(document('<line number="1" hits="0" />'))
    with pytest.raises(FrozenInstanceError):
        report.packages = ()
