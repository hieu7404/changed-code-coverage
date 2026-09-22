"""Verify strict whole-run coverage provenance validation."""

import hashlib
import json

import pytest

from tc1.errors import ProvenanceError
from tc1.provenance import read_provenance, verify_provenance


def _sidecar(coverage, commit, **overrides):
    document = {
        "schema_version": "1.0",
        "commit_sha": commit,
        "dirty_state": False,
        "collector": "coverlet.collector",
        "collector_version": "6.0.4",
        "collection_command": "dotnet test",
        "target_framework": "net10.0",
        "coverage_xml_sha256": hashlib.sha256(coverage.read_bytes()).hexdigest(),
        "timestamp": "2026-09-22T00:00:00Z",
        "run_id": "additional metadata is allowed",
    }
    document.update(overrides)
    path = coverage.with_suffix(".provenance.json")
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_matching_clean_sidecar_verifies_commit_and_coverage_hash(tmp_path):
    coverage = tmp_path / "coverage.xml"
    coverage.write_text("<coverage><packages/></coverage>", encoding="utf-8")
    commit = "a" * 40

    provenance = verify_provenance(_sidecar(coverage, commit), coverage, commit)

    assert provenance is not None
    assert provenance.commit_sha == commit
    assert provenance.coverage_xml_sha256 == hashlib.sha256(coverage.read_bytes()).hexdigest()


@pytest.mark.parametrize(("field", "value", "match"), [
    ("commit_sha", "b" * 40, "does not match analysis head"),
    ("dirty_state", True, "dirty_state is true"),
    ("coverage_xml_sha256", "0" * 64, "does not match the supplied coverage file"),
])
def test_invalid_sidecar_fails_the_entire_analysis_input(tmp_path, field, value, match):
    coverage = tmp_path / "coverage.xml"
    coverage.write_text("<coverage><packages/></coverage>", encoding="utf-8")
    sidecar = _sidecar(coverage, "a" * 40, **{field: value})

    with pytest.raises(ProvenanceError, match=match):
        verify_provenance(sidecar, coverage, "a" * 40)


def test_missing_or_malformed_required_metadata_is_rejected(tmp_path):
    coverage = tmp_path / "coverage.xml"
    coverage.write_text("<coverage><packages/></coverage>", encoding="utf-8")
    sidecar = _sidecar(coverage, "a" * 40)
    document = json.loads(sidecar.read_text(encoding="utf-8"))
    del document["target_framework"]
    sidecar.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ProvenanceError, match="missing required fields: target_framework"):
        read_provenance(sidecar)
    with pytest.raises(ProvenanceError, match="requires --provenance"):
        verify_provenance(None, coverage, "a" * 40, required=True)
