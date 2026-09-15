"""Parse a controlled Cobertura profile without inventing missing evidence.

Class-level and method-level entries remain separate. Duplicate records, raw
paths and branch attributes are preserved; classification belongs to the mapper.
"""

import re
from pathlib import Path
from xml.etree import ElementTree as ET

from tc1.errors import CoberturaError
from tc1.models import (
    ConditionEvidence, CoverageClass, CoverageMethod, CoveragePackage,
    CoverageReport, LineCoverage, SourceLocation,
)

_INTEGER = re.compile(r"[0-9]+")


def _attributes(element: ET.Element) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(element.attrib.items()))


def _integer(element: ET.Element, name: str, minimum: int) -> int:
    raw = element.get(name)
    if raw is None or not _INTEGER.fullmatch(raw):
        raise CoberturaError(f"line @{name} must be an explicit integer >= {minimum}")
    try:
        value = int(raw)
    except ValueError as exc:
        raise CoberturaError(f"line @{name} is not a supported integer") from exc
    if value < minimum:
        raise CoberturaError(f"line @{name} must be >= {minimum}")
    return value


class _TreeBuilder(ET.TreeBuilder):
    def doctype(self, name: str, pubid: str | None, system: str | None) -> None:
        # The validated Coverlet profile has no DTD. Never expand DTD-supplied evidence.
        raise CoberturaError("DOCTYPE declarations are not supported in the Cobertura profile")


class _Reader:
    def __init__(self, namespace: str):
        self.namespace = namespace

    def children(self, element: ET.Element, *allowed: str) -> None:
        if element.text and element.text.strip():
            raise CoberturaError(f"unexpected text inside {element.tag!r}")
        tags = {self.namespace + name for name in allowed}
        for child in element:
            if child.tag not in tags:
                raise CoberturaError(f"unsupported element {child.tag!r} inside {element.tag!r}")
            if child.tail and child.tail.strip():
                raise CoberturaError(f"unexpected text after {child.tag!r}")

    def one(self, element: ET.Element, name: str, *, required: bool = False) -> ET.Element | None:
        found = element.findall(self.namespace + name)
        if len(found) > 1:
            raise CoberturaError(f"multiple {name!r} containers inside {element.tag!r}")
        if not found and required:
            raise CoberturaError(f"missing {name!r} container inside {element.tag!r}")
        return found[0] if found else None

    def line(self, element: ET.Element, filename: str) -> LineCoverage:
        self.children(element, "conditions")
        number = _integer(element, "number", 1)
        hits = _integer(element, "hits", 0)
        conditions = self.one(element, "conditions")
        records = []
        if conditions is not None:
            self.children(conditions, "condition")
            for condition in conditions:
                self.children(condition)
                records.append(ConditionEvidence(
                    number=condition.get("number"), type=condition.get("type"),
                    coverage=condition.get("coverage"), attributes=_attributes(condition),
                ))
        return LineCoverage(
            location=SourceLocation(filename, number), hits=hits,
            condition_coverage=element.get("condition-coverage"),
            conditions=tuple(records), branch=element.get("branch"),
            attributes=_attributes(element),
        )

    def lines(self, parent: ET.Element, filename: str) -> tuple[tuple[LineCoverage, ...], bool]:
        container = self.one(parent, "lines")
        if container is None:
            return (), False
        self.children(container, "line")
        return tuple(self.line(element, filename) for element in container), True

    def coverage_class(self, element: ET.Element) -> CoverageClass:
        self.children(element, "methods", "lines")
        filename = element.get("filename")
        if filename is None or not filename.strip():
            raise CoberturaError("class @filename must be explicitly present and non-empty")
        lines, present = self.lines(element, filename)
        methods = []
        container = self.one(element, "methods")
        if container is not None:
            self.children(container, "method")
            for method in container:
                self.children(method, "lines")
                method_lines, method_present = self.lines(method, filename)
                methods.append(CoverageMethod(
                    name=method.get("name"), signature=method.get("signature"),
                    lines=method_lines, lines_present=method_present,
                    attributes=_attributes(method),
                ))
        return CoverageClass(
            filename=filename, name=element.get("name"), lines=lines,
            methods=tuple(methods), lines_present=present, attributes=_attributes(element),
        )

    def package(self, element: ET.Element) -> CoveragePackage:
        self.children(element, "classes")
        classes = self.one(element, "classes", required=True)
        assert classes is not None
        self.children(classes, "class")
        return CoveragePackage(
            name=element.get("name"),
            classes=tuple(self.coverage_class(item) for item in classes),
            attributes=_attributes(element),
        )

    def report(self, root: ET.Element) -> CoverageReport:
        self.children(root, "sources", "packages")
        source_container = self.one(root, "sources")
        sources = []
        if source_container is not None:
            self.children(source_container, "source")
            for source in source_container:
                if len(source):
                    raise CoberturaError("source must contain text only")
                sources.append(source.text if source.text is not None else "")
        packages = self.one(root, "packages", required=True)
        assert packages is not None
        self.children(packages, "package")
        return CoverageReport(
            sources=tuple(sources),
            packages=tuple(self.package(package) for package in packages),
            attributes=_attributes(root),
        )


def parse_cobertura(data: bytes) -> CoverageReport:
    """Parse XML bytes, honoring the encoding declaration and optional namespace.

    Missing lines remain missing. Required numeric evidence is strict; optional
    branch metadata remains raw even when contradictory or uninterpretable.
    """
    try:
        root = ET.fromstring(data, parser=ET.XMLParser(target=_TreeBuilder()))
    except (ET.ParseError, ValueError, LookupError) as exc:
        raise CoberturaError(f"invalid Cobertura XML: {exc}") from exc
    namespace = root.tag[:root.tag.index("}") + 1] if root.tag.startswith("{") else ""
    if root.tag != namespace + "coverage":
        raise CoberturaError("expected Cobertura root element 'coverage'")
    return _Reader(namespace).report(root)


def read_cobertura(path: Path | str) -> CoverageReport:
    """Read one local export. Relative input paths are relative to the caller's cwd."""
    source = Path(path)
    try:
        data = source.read_bytes()
    except (OSError, ValueError) as exc:
        raise CoberturaError(f"cannot read Cobertura file {str(source)!r}: {exc}") from exc
    try:
        return parse_cobertura(data)
    except CoberturaError as exc:
        raise CoberturaError(f"Cobertura file {str(source)!r}: {exc}") from exc
