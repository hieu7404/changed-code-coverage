"""Reviewed patch fixtures and rejection of malformed diff evidence."""

import json
from pathlib import Path

import pytest

from tc1.diff_parser import parse_file_patch, parse_raw_diff
from tc1.errors import DiffParseError
from tc1.models import ChangeKind

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
EXPECTED = json.loads((FIXTURES / "expected/git_diff.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", EXPECTED)
def test_reviewed_patch_fixture(name):
    parsed = parse_file_patch((FIXTURES / "diffs" / name).read_bytes())
    expected = EXPECTED[name]
    assert [line for hunk in parsed.hunks for line in hunk.added_lines] == expected["added"]
    assert [line for hunk in parsed.hunks for line in hunk.removed_lines] == expected["removed"]
    assert [[h.old_start, h.old_count, h.new_start, h.new_count] for h in parsed.hunks] == expected["ranges"]
    assert parsed.is_binary is expected["binary"]


def test_context_is_not_counted_as_changed():
    parsed = parse_file_patch(
        b"diff --git a/F.cs b/F.cs\n@@ -3,3 +3,3 @@ function\n same\n-old\n+new\n same\n"
    )
    assert parsed.hunks[0].added_lines == (4,)
    assert parsed.hunks[0].removed_lines == (4,)


def test_source_control_characters_do_not_create_extra_lines():
    parsed = parse_file_patch(
        b"diff --git a/F.cs b/F.cs\n@@ -1 +1 @@\n-old\r\n+new\x85\xff\r\n"
    )
    assert parsed.hunks[0].added_lines == (1,)


@pytest.mark.parametrize("body", [
    b"@@ -1,2 +1 @@\n-old\n+new\n",  # truncated old side
    b"@@ -1 +1 @@\n-old\n+new\n+extra\n",
    b"@@ -1 +1 @@\n+new\n+extra\n-old\n",
    b"@@ broken @@\n",
    b"@@ -0 +1 @@\n-old\n+new\n",
    b"@@ -1,0 +1,0 @@\n",
    b"@@ -1 +1 @@\n\\ No newline at end of file\n-old\n+new\n",
    b"@@ -1 +1 @@\n-old\n+new\n@@ -1 +1 @@\n-old\n+new\n",
    b"@@@ -1 -1 +1 @@@\n",
    b"Binary files a/F.cs and b/F.cs differ\n@@ -1 +1 @@\n-old\n+new\n",
    b"GIT binary patch\n",
    b"rename from F.cs\nrename to G.cs\n",
    b"unexpected output\n",
    b"diff --git a/G.cs b/G.cs\n",
])
def test_malformed_or_unsupported_patch_is_an_error(body):
    with pytest.raises(DiffParseError):
        parse_file_patch(b"diff --git a/F.cs b/F.cs\n" + body)


@pytest.mark.parametrize("data", [b"", b"@@ -1 +1 @@\n-old\n+new\n"])
def test_missing_file_header_is_an_error(data):
    with pytest.raises(DiffParseError):
        parse_file_patch(data)


def raw_record(path=b"F.cs", status=b"M", old_mode=b"100644", new_mode=b"100644"):
    return b":" + old_mode + b" " + new_mode + b" " + b"1" * 40 + b" " + b"2" * 40 + b" " + status + b"\0" + path + b"\0"


def test_raw_paths_are_exact_and_sorted():
    paths = ["z.cs", "source/a b\tquoted\"\nname.cs", "src/Đơn hàng [1].cs"]
    entries = parse_raw_diff(b"".join(raw_record(path.encode()) for path in paths))
    assert [entry.path for entry in entries] == sorted(paths)
    assert all(entry.kind is ChangeKind.MODIFIED for entry in entries)


@pytest.mark.parametrize("data", [
    raw_record()[:-1], raw_record() + b"bad\0",
    raw_record(status=b"R100"), raw_record(status=b"C100"), raw_record(status=b"U"),
    raw_record(path=b"../F.cs"), raw_record(path=b"/F.cs"), raw_record(path=b""),
    raw_record(path=b"a//F.cs"), raw_record(path=b"bad\xff.cs"),
    raw_record() + raw_record(),
    raw_record(status=b"A"), raw_record(status=b"D"),
])
def test_bad_raw_records_are_errors(data):
    with pytest.raises(DiffParseError):
        parse_raw_diff(data)


def test_empty_raw_diff_is_valid():
    assert parse_raw_diff(b"") == ()
