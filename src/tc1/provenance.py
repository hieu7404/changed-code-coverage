"""Read and verify metadata for one Cobertura collection run."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from tc1.errors import ProvenanceError
from tc1.models import CoverageProvenance

_COMMIT = re.compile(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}")
_SHA256 = re.compile(r"[0-9a-fA-F]{64}")
_REQUIRED = (
    "commit_sha", "dirty_state", "collector", "collector_version",
    "collection_command", "target_framework", "coverage_xml_sha256", "timestamp",
)


def _read_object(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProvenanceError(f"cannot read provenance sidecar {str(path)!r}: {exc}") from exc
    if not isinstance(document, dict):
        raise ProvenanceError("provenance sidecar must contain a JSON object")
    if document.get("schema_version") != "1.0":
        raise ProvenanceError("provenance sidecar schema_version must be '1.0'")
    missing = [name for name in _REQUIRED if name not in document]
    if missing:
        raise ProvenanceError("provenance sidecar is missing required fields: " + ", ".join(missing))
    return document


def read_provenance(path: Path | str) -> CoverageProvenance:
    """Parse one strict, portable provenance sidecar without validating its inputs."""
    document = _read_object(Path(path))
    commit = document["commit_sha"]
    checksum = document["coverage_xml_sha256"]
    if not isinstance(commit, str) or _COMMIT.fullmatch(commit) is None:
        raise ProvenanceError("provenance commit_sha must be a full 40- or 64-character Git commit ID")
    if not isinstance(checksum, str) or _SHA256.fullmatch(checksum) is None:
        raise ProvenanceError("provenance coverage_xml_sha256 must be a 64-character SHA-256 digest")
    if type(document["dirty_state"]) is not bool:
        raise ProvenanceError("provenance dirty_state must be a boolean")
    for name in ("collector", "collector_version", "collection_command", "target_framework", "timestamp"):
        if not isinstance(document[name], str) or not document[name].strip():
            raise ProvenanceError(f"provenance {name} must be a non-empty string")
    return CoverageProvenance(
        commit_sha=commit.lower(),
        dirty_state=document["dirty_state"],
        collector=document["collector"],
        collector_version=document["collector_version"],
        collection_command=document["collection_command"],
        target_framework=document["target_framework"],
        coverage_xml_sha256=checksum.lower(),
        timestamp=document["timestamp"],
    )


def verify_provenance(
    sidecar: Path | str | None, coverage: Path | str, head_commit: str, *, required: bool = False,
) -> CoverageProvenance | None:
    """Return verified sidecar metadata or fail before coverage findings are mapped."""
    if sidecar is None:
        if required:
            raise ProvenanceError("--require-provenance requires --provenance")
        return None
    provenance = read_provenance(sidecar)
    if provenance.dirty_state:
        raise ProvenanceError("provenance dirty_state is true; coverage was collected from a dirty worktree")
    if provenance.commit_sha != head_commit.lower():
        raise ProvenanceError(
            f"provenance commit_sha {provenance.commit_sha} does not match analysis head {head_commit}"
        )
    try:
        with Path(coverage).open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
    except (OSError, ValueError) as exc:
        raise ProvenanceError(f"cannot hash coverage file {str(coverage)!r}: {exc}") from exc
    if digest != provenance.coverage_xml_sha256:
        raise ProvenanceError("provenance coverage_xml_sha256 does not match the supplied coverage file")
    return provenance
