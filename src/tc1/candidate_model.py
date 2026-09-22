"""Opt-in, conservative source-form filtering for changed-line candidates.

The default model never reads source text.  This prototype only moves a finding out
of scope after TC1 has already established that it is unknown solely because the
collector has no explicit line entry.  It leaves ambiguous and executable-looking
source untouched.
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from tc1.errors import InputError
from tc1.git_diff import read_file_at_commit
from tc1.models import (
    AnalysisResult,
    CandidateModel,
    CoverageStatus,
    ExcludedLine,
)

_ATTRIBUTE = re.compile(r"^\[\s*[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*(?:\s*\(|\s*\])")
_TYPE_DECLARATION = re.compile(
    r"^(?:(?:public|private|protected|internal|static|abstract|sealed|partial|readonly)\s+)*"
    r"(?:class|interface|record|struct|enum)\b",
)
_CONST_DECLARATION = re.compile(r"^(?:(?:public|private|protected|internal|static|readonly)\s+)*const\b")
_METHOD_SIGNATURE = re.compile(
    r"^(?!(?:return|throw|new|await|yield|if|while|for|foreach|switch|using|lock|do)\b)"
    r"(?:(?:public|private|protected|internal|static|abstract|virtual|override|sealed|partial|async|unsafe|extern|new)\s+)*"
    r"[A-Za-z_]\w*(?:\s*<[^;{}=()]*>)?(?:[?\[\]]*)\s+[A-Za-z_]\w*\s*\(",
)
_PARAMETER_CONTINUATION = re.compile(
    r"^[A-Za-z_]\w*(?:\s*<[^;{}=()]*>)?(?:[?\[\]]*)\s+[A-Za-z_]\w*\s*(?:,|\))?$",
)
_UNINITIALIZED_LOCAL = re.compile(
    r"^[A-Za-z_]\w*(?:\s*<[^;{}=()]*>)?(?:[?\[\]]*)\s+[A-Za-z_]\w*\s*;$",
)
_CONTROL_LABEL = re.compile(
    r"^(?:else|try|finally|catch(?:\s*\([^)]*\))?|case\b.*:|default\s*:)(?:\s*\{|\s*//.*)?$",
)
_RAW_DELIMITER = re.compile(r'"{3,}')


def classify_csharp_source(source: str) -> tuple[str | None, ...]:
    """Return conservative source-form classifications indexed by one-based line.

    ``None`` means the prototype cannot safely exclude that line.  The scanner is
    intentionally lexical: it recognizes only forms audited in CRAP4CSharp and
    does not attempt to parse or prove C# executability.
    """
    forms: list[str | None] = []
    block_comment = False
    raw_delimiter: str | None = None
    for raw_line in source.splitlines():
        text = raw_line.strip()
        if raw_delimiter is not None:
            forms.append("raw_string_literal")
            if raw_delimiter in raw_line:
                raw_delimiter = None
            continue
        if block_comment:
            forms.append("comment")
            if "*/" in raw_line:
                block_comment = False
            continue
        if not text:
            forms.append("blank")
            continue
        if text.startswith(("//", "///", "/*", "*")):
            forms.append("comment")
            if text.startswith("/*") and "*/" not in text:
                block_comment = True
            continue
        raw_start = _RAW_DELIMITER.search(raw_line)
        if raw_start is not None:
            delimiter = raw_start.group(0)
            if delimiter not in raw_line[raw_start.end():]:
                raw_delimiter = delimiter
        if text in {"{", "}", "};"}:
            forms.append("brace")
        elif text.startswith(("using ", "global using ", "namespace ")):
            forms.append("using_or_namespace")
        elif text.startswith("#"):
            forms.append("directive")
        elif _ATTRIBUTE.match(text):
            forms.append("attribute")
        elif _CONTROL_LABEL.match(text):
            forms.append("control_flow_label")
        elif _TYPE_DECLARATION.match(text):
            forms.append("type_declaration")
        elif _CONST_DECLARATION.match(text):
            forms.append("const_declaration")
        elif _METHOD_SIGNATURE.match(text) or _PARAMETER_CONTINUATION.match(text):
            forms.append("declaration_or_signature")
        elif _UNINITIALIZED_LOCAL.match(text):
            forms.append("uninitialized_local_declaration")
        else:
            forms.append(None)
    return tuple(forms)


def apply_candidate_model(
    analysis: AnalysisResult, *, repo_root: Path, head_commit: str, model: CandidateModel,
) -> AnalysisResult:
    """Apply one explicit candidate model after evidence mapping.

    The executable prototype excludes only audited source forms from findings that
    are already ``unknown/no_explicit_line_evidence``.  Explicit coverage evidence,
    unmatched paths, and source forms outside the conservative lexical subset remain
    unchanged.  Model exclusions stay visible in ``excluded_lines``.
    """
    if model is CandidateModel.ALL_CHANGED_LINES:
        return replace(analysis, candidate_model=model)
    if model is not CandidateModel.EXECUTABLE_PROTOTYPE:
        raise InputError(f"unsupported candidate model: {model}")

    classifications: dict[str, tuple[str | None, ...]] = {}
    retained = []
    model_excluded = []
    for finding in analysis.lines:
        if not (
            finding.status is CoverageStatus.UNKNOWN
            and finding.reason == "no_explicit_line_evidence"
        ):
            retained.append(finding)
            continue
        forms = classifications.get(finding.location.path)
        if forms is None:
            try:
                source = read_file_at_commit(repo_root, head_commit, finding.location.path).decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise InputError(
                    "executable_prototype requires UTF-8 C# source: "
                    f"{finding.location.path}"
                ) from exc
            forms = classify_csharp_source(source)
            classifications[finding.location.path] = forms
        form = forms[finding.location.line - 1] if finding.location.line <= len(forms) else None
        if form is None:
            retained.append(finding)
            continue
        model_excluded.append(ExcludedLine(
            finding.location, f"candidate_model:executable_prototype:{form}",
        ))
    return replace(
        analysis,
        lines=tuple(retained),
        excluded_lines=analysis.excluded_lines + tuple(model_excluded),
        candidate_model=model,
    )
