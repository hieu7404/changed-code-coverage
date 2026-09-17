(() => {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const elements = {
    fileInput: byId("report-file"), loadShowcase: byId("load-showcase"), reportSource: byId("report-source"),
    sourceBadge: byId("source-badge"), loadError: byId("load-error"),
    base: byId("base-revision"), head: byId("head-revision"), schema: byId("schema-version"),
    lineCoverage: byId("line-coverage"), lineRatio: byId("line-ratio"), lineCounts: byId("line-counts"),
    branchCoverage: byId("branch-coverage"), branchRatio: byId("branch-ratio"), branchCounts: byId("branch-counts"),
    statusFilter: byId("status-filter"), pathFilter: byId("path-filter"), lineFindingCount: byId("line-finding-count"),
    lineFindings: byId("line-findings"), branchFindings: byId("branch-findings"), excludedFindings: byId("excluded-findings"),
    supportingEvidence: byId("supporting-evidence"),
  };

  const showcaseReport = JSON.parse(byId("showcase-report").textContent);
  const state = { report: null, reportSource: {} };
  function requireObject(value, label) { if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(`${label} must be an object.`); }
  function validateReport(report) {
    requireObject(report, "Report");
    if (typeof report.schema_version !== "string" || !report.schema_version) throw new Error("Report is missing schema_version.");
    requireObject(report.analysis, "analysis"); requireObject(report.metrics, "metrics"); requireObject(report.metrics.lines, "metrics.lines"); requireObject(report.metrics.branches, "metrics.branches");
    for (const field of ["lines", "branches", "excluded_lines"]) if (!Array.isArray(report[field])) throw new Error(`Report field ${field} must be an array.`);
  }
  function clearChildren(node) { node.replaceChildren(); }
  function appendCell(row, value, className) { const cell = document.createElement("td"); if (className) cell.className = className; cell.textContent = value; row.append(cell); return cell; }
  function appendEmptyRow(body, colspan, message) { const row = document.createElement("tr"); const cell = appendCell(row, message, "empty-state"); cell.colSpan = colspan; body.append(row); }
  function asText(value, fallback = "—") { return value === null || value === undefined || value === "" ? fallback : String(value); }
  function coverageText(value) { return typeof value === "number" ? `${value.toFixed(2)}%` : "N/A"; }
  function accuracyText(value) { return typeof value === "number" ? `${value.toFixed(1)}%` : "N/A"; }
  function showError(node, message) { node.textContent = message; }

  function renderMetric(summary, coverageNode, ratioNode, countNode) {
    coverageNode.textContent = coverageText(summary.coverage_percent);
    ratioNode.textContent = `${asText(summary.covered, "0")} covered / ${asText(summary.classifiable, "0")} classifiable`;
    clearChildren(countNode);
    for (const [label, key] of [["Candidates", "candidates"], ["Covered", "covered"], ["Uncovered", "uncovered"], ["Unknown", "unknown"], ["Excluded", "excluded"]]) {
      const term = document.createElement("div"); const definition = document.createElement("dt"); const value = document.createElement("dd");
      definition.textContent = label; value.textContent = asText(summary[key], "0"); term.append(definition, value); countNode.append(term);
    }
  }
  function renderContext(report) {
    elements.base.textContent = asText(report.analysis.base); elements.head.textContent = asText(report.analysis.head); elements.schema.textContent = report.schema_version;
    renderMetric(report.metrics.lines, elements.lineCoverage, elements.lineRatio, elements.lineCounts); renderMetric(report.metrics.branches, elements.branchCoverage, elements.branchRatio, elements.branchCounts);
  }
  function statusBadge(status) { const badge = document.createElement("span"); const known = ["covered", "uncovered", "unknown"].includes(status) ? status : "unknown"; badge.className = `status status-${known}`; badge.textContent = asText(status, "unknown"); return badge; }
  function renderLineFindings() {
    const lines = state.report.lines; const requestedStatus = elements.statusFilter.value; const requestedPath = elements.pathFilter.value.trim().toLowerCase();
    const visible = lines.filter((finding) => (requestedStatus === "all" || finding.status === requestedStatus) && (!requestedPath || String(finding.path || "").toLowerCase().includes(requestedPath)));
    elements.lineFindingCount.textContent = `${visible.length} of ${lines.length} findings`; clearChildren(elements.lineFindings);
    if (!visible.length) { appendEmptyRow(elements.lineFindings, 5, "No line findings match the current filters."); return; }
    for (const finding of visible) { const row = document.createElement("tr"); appendCell(row, asText(finding.path), "path-cell"); appendCell(row, asText(finding.line)); const cell = document.createElement("td"); cell.append(statusBadge(finding.status)); row.append(cell); appendCell(row, asText(finding.hits)); appendCell(row, asText(finding.reason)); elements.lineFindings.append(row); }
  }
  function renderBranches(report) {
    clearChildren(elements.branchFindings); if (!report.branches.length) { appendEmptyRow(elements.branchFindings, 4, "No changed branch findings were reported."); return; }
    for (const finding of report.branches) { const row = document.createElement("tr"); appendCell(row, asText(finding.path), "path-cell"); appendCell(row, asText(finding.line)); const aggregate = finding.aggregate; appendCell(row, aggregate && typeof aggregate === "object" ? `${asText(aggregate.covered, "0")} / ${asText(aggregate.total, "0")}` : "unknown"); appendCell(row, asText(finding.reason)); elements.branchFindings.append(row); }
  }
  function renderExclusions(report) {
    clearChildren(elements.excludedFindings); if (!report.excluded_lines.length) { appendEmptyRow(elements.excludedFindings, 3, "No changed lines were excluded."); return; }
    for (const finding of report.excluded_lines) { const row = document.createElement("tr"); appendCell(row, asText(finding.path), "path-cell"); appendCell(row, asText(finding.line)); appendCell(row, asText(finding.reason)); elements.excludedFindings.append(row); }
  }
  function resolveEvidenceUrl(path) { if (!state.reportSource.url) return null; try { return new URL(path, state.reportSource.url).href; } catch (_) { return null; } }
  function renderSupportingEvidence(report) {
    clearChildren(elements.supportingEvidence); const evidence = report.supporting_evidence;
    if (!evidence || !evidence.report_generator_html) { elements.supportingEvidence.textContent = "No ReportGenerator supporting evidence was declared in this report."; return; }
    const path = evidence.report_generator_html;
    if (evidence.available && state.reportSource.url) { const link = document.createElement("a"); link.href = resolveEvidenceUrl(path) || path; link.textContent = "Open ReportGenerator coverage HTML"; elements.supportingEvidence.append(link, document.createTextNode(` (${path})`)); return; }
    const code = document.createElement("code"); code.textContent = path;
    elements.supportingEvidence.append(document.createTextNode(evidence.available ? "ReportGenerator evidence is available, but a locally uploaded report cannot resolve its relative link: " : "ReportGenerator evidence was unavailable when TC1 generated this report: "), code);
  }
  function reportSourceDescription(source) { if (source.kind === "upload") return `Loaded local TC1 report: ${source.name}.`; if (source.kind === "url") return `Loaded live TC1 report from ${source.url}.`; return "Bundled synthetic showcase: representative data only, not a claim about a real repository."; }
  function loadReport(report, source) {
    validateReport(report); state.report = report; state.reportSource = source; elements.reportSource.textContent = reportSourceDescription(source); showError(elements.loadError, "");
    renderContext(report); renderLineFindings(); renderBranches(report); renderExclusions(report); renderSupportingEvidence(report);
  }
  async function loadReportFile(file) { try { const report = JSON.parse(await file.text()); loadReport(report, { kind: "upload", name: file.name }); } catch (error) { showError(elements.loadError, `Could not load ${file.name}: ${error.message}`); } }
  async function loadQueryReport(parameter) { try { const url = new URL(parameter, window.location.href).href; const response = await fetch(url); if (!response.ok) throw new Error(`HTTP ${response.status}`); loadReport(await response.json(), { kind: "url", url }); } catch (error) { showError(elements.loadError, `Could not load the report from the URL parameter: ${error.message}`); } }

  elements.fileInput.addEventListener("change", () => { const [file] = elements.fileInput.files; if (file) loadReportFile(file); });
  elements.loadShowcase.addEventListener("click", () => { elements.fileInput.value = ""; loadReport(showcaseReport, { kind: "showcase" }); });
  elements.statusFilter.addEventListener("change", renderLineFindings); elements.pathFilter.addEventListener("input", renderLineFindings);

  loadReport(showcaseReport, { kind: "showcase" });
  const query = new URLSearchParams(window.location.search); const reportParameter = query.get("report");
  if (reportParameter) loadQueryReport(reportParameter);
})();
