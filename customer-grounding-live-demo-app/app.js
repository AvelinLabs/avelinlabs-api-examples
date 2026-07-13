(() => {
  const SUCCESSFUL_RUN_STATUSES = new Set(["completed", "skipped"]);
  const ACTIVE_SOURCE_STATUSES = new Set(["active"]);
  const CHECKLIST_STEPS = [
    ["connected", "Connected"],
    ["sourceCreated", "Context registered"],
    ["contextIngested", "Context ready"],
    ["reportGenerated", "Intelligence generated"],
    ["evidenceReturned", "Evidence returned"],
    ["traceAvailable", "Trace reviewed"],
    ["cleanupCompleted", "Demo data removed"],
  ];

  const state = {
    samples: [],
    sample: null,
    sourceId: "",
    traceId: "",
    decisionId: "",
    report: null,
    trace: null,
    usage: null,
    activeSnippet: "curl-source",
    connectionConfirmed: false,
    sourceCreatedInSession: false,
    sourceSelectedIntentionally: false,
    source: null,
    ingestionRuns: [],
    successfulRun: null,
    artifacts: [],
    ingestionCompleted: false,
    sourceActive: false,
    documentsIngested: false,
    reportGenerated: false,
    evidenceReturned: false,
    traceAvailable: false,
    cleanupCompleted: false,
    lastEvidenceCount: 0,
  };

  const $ = (id) => document.getElementById(id);

  function setText(id, value) {
    const element = $(id);
    if (element) element.textContent = value == null || value === "" ? "-" : String(value);
  }

  function setStatus(id, message, type = "muted") {
    const element = $(id);
    if (!element) return;
    element.className = `status-box ${type}`;
    element.textContent = message;
  }

  function setAlert(message = "", type = "muted") {
    const element = $("grounding-alert");
    if (!element) return;
    element.hidden = !message;
    element.className = `status-box ${type}`;
    element.textContent = message;
  }

  async function api(path, options = {}) {
    const response = await fetch(path, {
      ...options,
      headers: options.body instanceof FormData ? options.headers : { "Content-Type": "application/json", ...(options.headers || {}) },
    });
    const text = await response.text();
    const data = text ? JSON.parse(text) : {};
    if (!response.ok) {
      const error = new Error(data.detail || data.error || `HTTP ${response.status}`);
      error.payload = data;
      error.status = response.status;
      throw error;
    }
    return data;
  }

  function pretty(value) {
    return JSON.stringify(value, null, 2);
  }

  function splitFocusAreas(value) {
    return String(value || "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function generatedSourceId() {
    const role = ($("role-title").value || "role").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 36);
    return `cg-live-${role || "source"}-${Date.now().toString(36)}`;
  }

  function sanitizeSourceId(value) {
    return String(value || "").trim().replace(/[^a-zA-Z0-9_.-]/g, "-");
  }

  function currentSourceInput() {
    return sanitizeSourceId($("source-id").value);
  }

  function currentRoleContext() {
    const roleContext = $("role-context").value.trim();
    const question = $("business-question").value.trim();
    return [roleContext, question ? `Business question: ${question}` : ""].filter(Boolean).join("\n\n");
  }

  function renderKeyValues(container, values) {
    if (!container) return;
    const dl = document.createElement("dl");
    dl.className = "key-value";
    values.forEach(([key, value]) => {
      const row = document.createElement("div");
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = key;
      dd.textContent = value == null || value === "" ? "-" : String(value);
      row.append(dt, dd);
      dl.appendChild(row);
    });
    container.replaceChildren(dl);
  }

  function card(title, body, meta, className = "") {
    const article = document.createElement("article");
    if (className) article.className = className;
    const h3 = document.createElement("h3");
    const p = document.createElement("p");
    h3.textContent = title;
    p.textContent = body || "-";
    article.append(h3, p);
    if (meta) {
      const small = document.createElement("small");
      small.textContent = meta;
      article.appendChild(small);
    }
    return article;
  }

  function pills(containerId, items) {
    const container = $(containerId);
    if (!container) return;
    container.replaceChildren();
    const list = Array.isArray(items) ? items : [];
    if (!list.length) {
      const span = document.createElement("span");
      span.className = "pill";
      span.textContent = "No flags returned";
      container.appendChild(span);
      return;
    }
    list.forEach((item) => {
      const span = document.createElement("span");
      span.className = "pill";
      span.textContent = String(item);
      container.appendChild(span);
    });
  }

  function formatTimestamp(value) {
    const raw = String(value || "").trim();
    if (!raw || raw === "null" || raw.startsWith("1970-01-01")) return "not provided by API";
    return raw;
  }

  function artifactCount() {
    const runArtifacts = Number(state.successfulRun?.artifact_count ?? 0);
    return Math.max(state.artifacts.length, Number.isFinite(runArtifacts) ? runArtifacts : 0);
  }

  function hasConfirmedSourceIntent() {
    return state.sourceCreatedInSession || state.sourceSelectedIntentionally;
  }

  function readyToGenerate() {
    return Boolean(
      state.sourceId &&
        hasConfirmedSourceIntent() &&
        state.sourceActive &&
        state.ingestionCompleted &&
        state.documentsIngested &&
        state.successfulRun
    );
  }

  function gateMessage() {
    return "Prepare customer context before generating grounded intelligence.";
  }

  function resetReportState() {
    state.report = null;
    state.trace = null;
    state.traceId = "";
    state.decisionId = "";
    state.reportGenerated = false;
    state.evidenceReturned = false;
    state.traceAvailable = false;
    state.lastEvidenceCount = 0;
    setAlert("");
    renderChecklist();
  }

  function resetSourceTracking(message) {
    state.sourceId = "";
    state.sourceCreatedInSession = false;
    state.sourceSelectedIntentionally = false;
    state.source = null;
    state.ingestionRuns = [];
    state.successfulRun = null;
    state.artifacts = [];
    state.ingestionCompleted = false;
    state.sourceActive = false;
    state.documentsIngested = false;
    state.cleanupCompleted = false;
    resetReportState();
    renderSourceState(message || "No customer context prepared yet.");
    updateGenerateGate();
  }

  function renderChecklist() {
    const list = $("demo-checklist");
    if (!list) return;
    const status = {
      connected: state.connectionConfirmed,
      sourceCreated: hasConfirmedSourceIntent() && Boolean(state.source),
      contextIngested: state.ingestionCompleted && state.documentsIngested,
      reportGenerated: state.reportGenerated,
      evidenceReturned: state.evidenceReturned,
      traceAvailable: state.traceAvailable,
      cleanupCompleted: state.cleanupCompleted,
    };
    const detail = {
      connected: status.connected ? "Connection verified" : "Waiting for connection test",
      sourceCreated: status.sourceCreated ? "Customer context registered" : "No context prepared",
      contextIngested: status.contextIngested ? `${artifactCount()} evidence segment(s) ready` : "Context not processed",
      reportGenerated: status.reportGenerated ? "Grounded result generated" : "Not generated",
      evidenceReturned: status.evidenceReturned ? `${state.lastEvidenceCount} evidence item(s)` : "No evidence confirmed",
      traceAvailable: status.traceAvailable ? "Trace reviewed" : "Trace not reviewed",
      cleanupCompleted: status.cleanupCompleted ? "Demo context removed" : "Demo context retained",
    };
    list.replaceChildren();
    CHECKLIST_STEPS.forEach(([id, label]) => {
      const item = document.createElement("li");
      item.className = status[id] ? "complete" : "pending";
      const marker = document.createElement("span");
      marker.className = "check-marker";
      marker.textContent = status[id] ? "OK" : "-";
      const text = document.createElement("span");
      text.textContent = label;
      const small = document.createElement("small");
      small.textContent = detail[id];
      item.append(marker, text, small);
      list.appendChild(item);
    });
  }

  function updateGenerateGate() {
    const button = $("generate-report");
    const gate = $("generate-gate");
    const ready = readyToGenerate();
    if (button) {
      button.disabled = !ready;
      button.title = ready ? "" : gateMessage();
    }
    if (gate) {
      gate.textContent = ready ? "Customer context is ready. You can generate grounded intelligence." : gateMessage();
      gate.className = ready ? "gate-note ready" : "gate-note blocked";
    }
    renderChecklist();
  }

  function missingReadinessReasons() {
    const reasons = [];
    if (!state.sourceId) reasons.push("context identifier not confirmed");
    if (!hasConfirmedSourceIntent()) reasons.push("context not prepared or selected");
    if (!state.sourceActive) reasons.push("context is not active");
    if (!state.ingestionCompleted) reasons.push("context processing has not completed");
    if (!state.documentsIngested) reasons.push("no evidence segments are available");
    return reasons;
  }

  function renderSourceState(message) {
    const ready = readyToGenerate();
    renderKeyValues($("run-metadata"), [
      ["Context status", state.source?.status || "not prepared"],
      ["Processing status", state.successfulRun?.status || "not completed"],
      ["Evidence segments", state.documentsIngested ? artifactCount() : 0],
      ["Ready to generate", ready ? "yes" : "no"],
    ]);
    const runMetadata = $("run-metadata");
    if (runMetadata) runMetadata.className = ready ? "status-box success" : "status-box warning";
    const run = state.successfulRun || state.ingestionRuns[0] || {};
    renderKeyValues($("advanced-source-details"), [
      ["source_id", state.sourceId],
      ["ingestion_run_id", run.ingestion_run_id],
      ["source_version_id", run.source_version_id || state.source?.active_version_id],
      ["parser", run.parser_version],
      ["content_type", run.content_type],
      ["artifact_count", artifactCount()],
      ["source_created_at", formatTimestamp(state.source?.created_at)],
      ["source_updated_at", formatTimestamp(state.source?.updated_at)],
    ]);
    if (message) setStatus("ingestion-status", message, ready ? "success" : "warning");
  }

  function applySourceStatus({ source, ingestionRuns, artifacts, selected, createdInSession }) {
    state.source = source || null;
    state.sourceId = source?.source_id || state.sourceId || currentSourceInput();
    if (state.sourceId) $("source-id").value = state.sourceId;
    if (createdInSession) {
      state.sourceCreatedInSession = true;
      state.sourceSelectedIntentionally = false;
    } else if (selected) {
      state.sourceSelectedIntentionally = true;
      state.sourceCreatedInSession = false;
    }
    state.ingestionRuns = Array.isArray(ingestionRuns) ? ingestionRuns : [];
    state.artifacts = Array.isArray(artifacts) ? artifacts : [];
    state.sourceActive = ACTIVE_SOURCE_STATUSES.has(source?.status || "");
    state.successfulRun =
      state.ingestionRuns.find((run) => SUCCESSFUL_RUN_STATUSES.has(run.status) && Number(run.artifact_count || 0) > 0) ||
      state.ingestionRuns.find((run) => SUCCESSFUL_RUN_STATUSES.has(run.status)) ||
      null;
    state.ingestionCompleted = Boolean(state.successfulRun);
    state.documentsIngested = artifactCount() > 0;
  }

  async function refreshSourceStatus(sourceId, options = {}) {
    const safeSourceId = sanitizeSourceId(sourceId);
    if (!safeSourceId) throw new Error(gateMessage());
    setStatus("ingestion-status", "Checking customer context readiness...", "warning");
    const readinessPayload = await api(`/local-api/sources/${encodeURIComponent(safeSourceId)}/readiness`);
    applySourceStatus({
      source: readinessPayload.source,
      ingestionRuns: readinessPayload.ingestion_runs || [],
      artifacts: readinessPayload.artifacts || [],
      selected: options.selected === true,
      createdInSession: options.createdInSession === true,
    });
    const ready = readyToGenerate();
    const message = ready
      ? `Customer context ready with ${artifactCount()} evidence segment(s). You can generate grounded intelligence.`
      : `Customer context is not ready: ${missingReadinessReasons().join("; ")}.`;
    renderSourceState(message);
    updateGenerateGate();
    updateSnippets();
    return ready;
  }

  async function loadHealth() {
    const health = await api("/local-api/health");
    if (health.config?.base_url) $("base-url").value = health.config.base_url;
    if (health.config?.api_key_configured) {
      setText("connection-status", `API key configured for this session (${health.config.api_key_preview}). Test the connection to continue.`);
    }
  }

  async function loadSamples() {
    const data = await api("/local-api/samples");
    state.samples = data.samples || [];
    const select = $("sample-select");
    select.replaceChildren();
    state.samples.forEach((sample) => {
      const option = document.createElement("option");
      option.value = sample.sample_id;
      option.textContent = sample.title;
      select.appendChild(option);
    });
    if (state.samples.length) await selectSample(state.samples[0].sample_id);
  }

  async function selectSample(sampleId) {
    if (!sampleId) return;
    const data = await api(`/local-api/samples/${encodeURIComponent(sampleId)}`);
    state.sample = data.sample;
    $("context-text").value = state.sample.content || "";
    $("role-title").value = state.sample.suggested_role_title || "";
    $("role-context").value = state.sample.suggested_role_context || "";
    $("business-question").value = state.sample.suggested_business_question || "";
    $("focus-areas").value = (state.sample.focus_areas || []).join(", ");
    $("source-id").value = generatedSourceId();
    $("sample-summary").textContent = state.sample.why_grounding_matters || "Synthetic sample loaded.";
    resetSourceTracking("No customer context prepared yet. Select Prepare grounded context before generating.");
    renderOfflinePreview();
    updateSnippets();
  }

  async function saveConfig() {
    const payload = {
      base_url: $("base-url").value.trim(),
      runtime_api_key: $("api-key").value.trim(),
    };
    const data = await api("/local-api/session", { method: "POST", body: JSON.stringify(payload) });
    $("api-key").value = "";
    state.connectionConfirmed = false;
    renderChecklist();
    setText(
      "connection-status",
      data.config.api_key_configured
        ? `Connection saved for ${data.config.base_url}. The API key is kept only for this local session.`
        : `API Base URL saved for ${data.config.base_url}. Enter the API key provided by AvelinLabs to continue.`
    );
  }

  async function testConnection() {
    setText("connection-status", "Testing connection to Customer Grounding...");
    await api("/local-api/capabilities");
    state.connectionConfirmed = true;
    setText("connection-status", "Connected. Customer Grounding is available.");
    renderChecklist();
  }

  async function createAndIngest() {
    const sourceId = currentSourceInput() || generatedSourceId();
    $("source-id").value = sourceId;
    state.sourceId = "";
    state.sourceCreatedInSession = false;
    state.sourceSelectedIntentionally = false;
    state.cleanupCompleted = false;
    resetReportState();
    setStatus("ingestion-status", "Preparing customer context...", "warning");
    const file = $("context-file").files[0];
    const sourcePayload = {
      source_id: sourceId,
      source_type: file ? "customer_file" : "customer_text",
      title: state.sample?.title || `Customer Grounding Live Demo - ${$("role-title").value || "Role Context"}`,
      owner: "local-live-demo",
      permissions_scope: "customer_private",
      retention_class: "short_lived",
      metadata: { example: "customer-grounding-live-demo-app", sample_id: state.sample?.sample_id || "custom" },
    };
    const created = await api("/local-api/sources", { method: "POST", body: JSON.stringify(sourcePayload) });
    state.sourceId = created.source?.source_id || sourceId;
    state.source = created.source || null;
    state.sourceCreatedInSession = true;
    $("source-id").value = state.sourceId;
    setStatus("ingestion-status", "Customer context registered. Processing content...", "warning");
    if (file) {
      const form = new FormData();
      form.append("source_id", state.sourceId);
      form.append("version_label", "live-demo-file-v1");
      form.append("metadata_json", JSON.stringify(sourcePayload.metadata));
      form.append("file", file);
      await api("/local-api/ingest-file", { method: "POST", body: form, headers: {} });
    } else {
      await api("/local-api/ingest-text", {
        method: "POST",
        body: JSON.stringify({
          source_id: state.sourceId,
          text: $("context-text").value,
          content_type: "text/markdown",
          version_label: "live-demo-text-v1",
          metadata: sourcePayload.metadata,
        }),
      });
    }
    await refreshSourceStatus(state.sourceId, { createdInSession: true });
  }

  async function refreshSelectedSource() {
    const sourceId = currentSourceInput();
    if (!sourceId) throw new Error(gateMessage());
    resetReportState();
    await refreshSourceStatus(sourceId, { selected: true });
  }

  async function generateReport() {
    if (!readyToGenerate()) {
      setStatus("ingestion-status", gateMessage(), "error");
      setAlert(gateMessage(), "error");
      updateGenerateGate();
      return;
    }
    setText("result-mode", "Generating grounded Role Intelligence...");
    setAlert("");
    const payload = {
      role_title: $("role-title").value.trim(),
      role_context: currentRoleContext(),
      focus_areas: splitFocusAreas($("focus-areas").value),
      source_ids: [state.sourceId],
      top_k: 5,
    };
    state.report = await api("/local-api/reports", { method: "POST", body: JSON.stringify(payload) });
    state.traceId = state.report.trace_id || state.report.trace?.trace_id || "";
    state.decisionId = state.report.trace?.decision_id || "";
    state.reportGenerated = true;
    renderReport(state.report, false);
    updateSnippets();
    renderChecklist();
  }

  function renderOfflinePreview() {
    const role = $("role-title").value || state.sample?.suggested_role_title || "Selected role";
    setText("result-mode", "Preview example - no API call has been made.");
    setAlert("");
    setText("executive-summary", state.sample?.why_grounding_matters || "Connect to AvelinLabs to generate grounded intelligence from this context.");
    setText("generic-title", `Generic ${role} answer`);
    setText("generic-copy", "A broad answer can describe responsibilities but usually misses the customer's operating model, evidence, confidence, and review flags.");
    setText("grounded-title", "Grounded output after live generation");
    setText("grounded-copy", state.sample?.why_grounding_matters || "The live report will use the selected source and return evidence-backed role criteria.");
    setText("confidence-card", "Confidence appears after generation.");
    setText("result-status-card", "No grounded result generated yet.");
    const advancedResult = $("advanced-result-details");
    if (advancedResult) advancedResult.textContent = "Trace and decision IDs appear after generation.";
    const criteria = $("criteria-list");
    criteria.replaceChildren(card("Expected grounded value", state.sample?.suggested_business_question || "The grounded result will show evidence-backed findings."));
    const evidence = $("evidence-list");
    evidence.replaceChildren(card("Evidence preview", "Evidence appears after the customer context is prepared and intelligence is generated."));
    pills("review-flags", ["Human review required", "Preview only"]);
  }

  function reportEvidenceItems(payload) {
    const items = [];
    const seen = new Set();
    [...(payload.evidence_references || []), ...(payload.evidence_snapshots || [])].forEach((item) => {
      const key = item.evidence_id || `${item.source_id}:${item.artifact_id}:${item.excerpt || item.excerpt_snapshot}`;
      if (!key || seen.has(key)) return;
      seen.add(key);
      items.push(item);
    });
    return items;
  }

  function reportFlags(payload, report, trace) {
    return payload.review_flags || report.review_flags || trace.review_flags || [];
  }

  function analyzeReport(payload) {
    const report = payload.report || payload.draft || {};
    const trace = payload.trace || {};
    const evidence = reportEvidenceItems(payload);
    const criteria = Array.isArray(report.key_role_criteria) ? report.key_role_criteria : [];
    const flags = reportFlags(payload, report, trace);
    const summary = String(report.grounded_summary || "");
    const missingEvidence =
      evidence.length === 0 ||
      flags.includes("missing_customer_grounding_evidence") ||
      summary.includes("No tenant-scoped customer grounding evidence was found");
    const missingCriteria = criteria.length === 0;
    return { report, trace, evidence, criteria, flags, missingEvidence, missingCriteria, demoReady: !missingEvidence && !missingCriteria };
  }

  function renderReport(payload, traceOnly) {
    const analysis = analyzeReport(payload);
    const { report, trace, evidence, criteria, flags, missingEvidence, missingCriteria, demoReady } = analysis;
    state.traceId = payload.trace_id || trace.trace_id || state.traceId;
    state.decisionId = trace.decision_id || report.decision_id || state.decisionId;
    state.evidenceReturned = evidence.length > 0;
    state.lastEvidenceCount = evidence.length;

    if (demoReady) {
      setText("result-mode", traceOnly ? "Trace reviewed. Grounded evidence confirmed." : "Grounded evidence found. The result is supported by customer context.");
      setAlert(`Grounded evidence found. ${evidence.length} evidence item(s) support this result.`, "success");
      setText("grounded-title", "Grounded evidence found");
      setText("grounded-copy", report.grounded_summary || "Evidence-backed summary returned.");
    } else if (missingEvidence) {
      setText("result-mode", "Ungrounded fallback / needs review.");
      setAlert("No grounding evidence was returned. Do not use this result for a decision.", "error");
      setText("grounded-title", "Ungrounded fallback / needs review");
      setText("grounded-copy", report.grounded_summary || "No grounding evidence was returned. Human review is required.");
    } else if (missingCriteria) {
      setText("result-mode", "Evidence returned, but criteria extraction needs review.");
      setAlert("Grounding evidence was returned, but no criteria were extracted. Treat this as needs review, not a success demo state.", "warning");
      setText("grounded-title", "Evidence found / criteria need review");
      setText("grounded-copy", report.grounded_summary || "Evidence exists, but criteria were not returned.");
    }

    setText("executive-summary", report.grounded_summary || "No grounded summary returned.");
    const confidence = report.confidence || {};
    renderKeyValues($("confidence-card"), [
      ["level", confidence.level],
      ["score", confidence.score],
      ["uncertainty", report.uncertainty?.level],
    ]);
    renderKeyValues($("result-status-card"), [
      ["Grounding state", demoReady ? "grounded evidence found" : "needs review"],
      ["Evidence returned", evidence.length],
      ["Criteria returned", criteria.length],
      ["Trace", state.traceId ? "available after fetch" : "not returned"],
    ]);
    renderKeyValues($("advanced-result-details"), [
      ["source_id", (report.source_ids || [state.sourceId]).join(", ")],
      ["trace_id", state.traceId],
      ["decision_id", state.decisionId],
      ["decision_type", trace.decision_type],
      ["access_channel", trace.access_channel],
      ["trace_created_at", formatTimestamp(trace.created_at)],
    ]);

    const criteriaList = $("criteria-list");
    criteriaList.replaceChildren();
    criteria.forEach((item) => {
      criteriaList.appendChild(
        card(
          item.text || "Grounded criterion",
          `Focus areas: ${(item.focus_areas || []).join(", ") || "-"}`,
          `Evidence: ${(item.evidence_ids || []).join(", ") || "-"}`,
          demoReady ? "criterion-card" : "criterion-card warning-card"
        )
      );
    });
    if (!criteriaList.children.length) {
      criteriaList.appendChild(card("No findings returned", "No grounded findings were returned. Human review is required.", "", "warning-card"));
    }

    const evidenceList = $("evidence-list");
    evidenceList.replaceChildren();
    evidence.forEach((item) => {
      const excerpt = item.excerpt || item.excerpt_snapshot || "No excerpt returned.";
      const source = item.source_title || item.source_id || "Unknown source";
      const document = [item.source_version, item.citation_locator, item.artifact_id].filter(Boolean).join(" | ");
      const reason = item.retrieval_reason || item.support_relationship || item.evidence_id || "";
      evidenceList.appendChild(
        card(
          source,
          excerpt,
          [document ? `Document: ${document}` : "", reason ? `Reason: ${reason}` : ""].filter(Boolean).join("  "),
          "evidence-card"
        )
      );
    });
    if (!evidenceList.children.length) {
      evidenceList.appendChild(card("No evidence returned", "No grounding evidence was returned. Do not use this result for a decision.", "", "warning-card"));
    }
    pills("review-flags", flags);
    renderChecklist();
  }

  async function fetchTrace() {
    if (!state.traceId) throw new Error("Generate grounded intelligence before reviewing traceability.");
    const payload = await api(`/local-api/traces/${encodeURIComponent(state.traceId)}`);
    state.trace = payload;
    state.traceAvailable = Boolean(payload.trace?.trace_id);
    renderReport({ ...payload, report: state.report?.report || state.report?.draft || {}, trace_id: state.traceId }, true);
    const trace = payload.trace || {};
    const evidenceCount = (payload.evidence_snapshots || []).length;
    renderKeyValues($("trace-view"), [
      ["Trace status", state.traceAvailable ? "reviewed" : "not available"],
      ["Evidence snapshots", evidenceCount],
      ["Review flags", (trace.review_flags || []).join(", ") || "none returned"],
      ["Created at", formatTimestamp(trace.created_at)],
    ]);
    $("trace-view").className = state.traceAvailable ? "status-box success" : "status-box warning";
    renderKeyValues($("advanced-trace-details"), [
      ["trace_id", trace.trace_id],
      ["decision_id", trace.decision_id],
      ["visibility", trace.trace_visibility],
      ["source_ids", (trace.source_ids || []).join(", ")],
      ["artifact_ids", (trace.artifact_ids || []).join(", ")],
    ]);
    renderChecklist();
  }

  async function fetchUsage() {
    const payload = await api("/local-api/usage");
    state.usage = payload;
    renderKeyValues($("usage-view"), [
      ["Account active sources", payload.sources?.active],
      ["Account ingestion runs", payload.ingestion?.runs],
      ["Account reports generated", payload.reports?.generated],
      ["Account traces created", payload.traces?.created],
      ["Request total", payload.request_usage?.total],
    ]);
    $("usage-view").className = "status-box success";
  }

  async function cleanupSource() {
    const sourceId = state.sourceId || currentSourceInput();
    if (!sourceId) throw new Error("No demo context is available to remove.");
    const payload = await api(`/local-api/sources/${encodeURIComponent(sourceId)}`, {
      method: "DELETE",
      body: JSON.stringify({ reason: "customer grounding live demo cleanup" }),
    });
    const deleted = payload.source?.status === "deleted" || payload.deletion?.status === "completed";
    state.cleanupCompleted = deleted;
    state.sourceCreatedInSession = false;
    state.sourceSelectedIntentionally = false;
    state.sourceActive = false;
    state.ingestionCompleted = false;
    state.documentsIngested = false;
    state.successfulRun = null;
    state.source = payload.source || state.source;
    setStatus(
      "cleanup-status",
      deleted ? "Demo context removed successfully." : "Demo context removal requested.",
      deleted ? "success" : "warning"
    );
    setStatus("ingestion-status", "Demo context removed. Prepare new customer context to generate another result.", "warning");
    $("source-id").value = generatedSourceId();
    state.sourceId = "";
    renderSourceState();
    updateGenerateGate();
    updateSnippets();
  }

  function snippets() {
    const base = $("base-url").value.trim() || "$BASE_URL";
    const sourceId = state.sourceId || currentSourceInput() || "<SOURCE_ID>";
    const title = state.sample?.title || "Customer Grounding Live Demo Source";
    const roleTitle = $("role-title").value.trim() || "<ROLE_TITLE>";
    const roleContext = currentRoleContext() || "<ROLE_CONTEXT>";
    const focusAreas = splitFocusAreas($("focus-areas").value);
    return {
      "curl-source": `curl -sS -X POST "${base}/api/v1/grounding/sources" \\
  -H "Authorization: Bearer $AVELIN_API_KEY" \\
  -H "Content-Type: application/json" \\
  --data '{
    "source_id": "${sourceId}",
    "source_type": "customer_text",
    "title": "${title}",
    "owner": "local-live-demo",
    "permissions_scope": "customer_private",
    "retention_class": "short_lived",
    "metadata": {"example": "customer-grounding-live-demo-app"}
  }'`,
      "curl-ingest": `curl -sS -X POST "${base}/api/v1/grounding/sources/${sourceId}/ingest-text" \\
  -H "Authorization: Bearer $AVELIN_API_KEY" \\
  -H "Content-Type: application/json" \\
  --data '{
    "content_type": "text/markdown",
    "version_label": "live-demo-text-v1",
    "text": "<SYNTHETIC_OR_APPROVED_CONTEXT>"
  }'`,
      "curl-report": `curl -sS -X POST "${base}/api/v1/grounding/role-intelligence/reports" \\
  -H "Authorization: Bearer $AVELIN_API_KEY" \\
  -H "Content-Type: application/json" \\
  --data '${pretty({
        role_title: roleTitle,
        role_context: roleContext,
        focus_areas: focusAreas,
        source_ids: [sourceId],
        top_k: 5,
      })}'`,
      "mcp-flow": pretty([
        {
          tool: "avelin_register_grounding_source",
          arguments: { source_id: sourceId, source_type: "customer_text", title, owner: "local-live-demo" },
        },
        {
          tool: "avelin_ingest_grounding_text",
          arguments: { source_id: sourceId, content_type: "text/markdown", version_label: "live-demo-text-v1", text: "<SYNTHETIC_OR_APPROVED_CONTEXT>" },
        },
        {
          tool: "avelin_generate_grounded_role_intelligence",
          arguments: { role_title: roleTitle, role_context: roleContext, focus_areas: focusAreas, source_ids: [sourceId], top_k: 5 },
        },
        {
          tool: "avelin_get_grounding_trace",
          arguments: { trace_id: state.traceId || "<TRACE_ID>" },
        },
      ]),
    };
  }

  function updateSnippets() {
    $("snippet-code").textContent = snippets()[state.activeSnippet];
  }

  function bind() {
    $("sample-select").addEventListener("change", (event) => selectSample(event.target.value).catch(showError));
    $("save-config").addEventListener("click", () => saveConfig().catch(showError));
    $("test-connection").addEventListener("click", () => testConnection().catch(showError));
    $("create-ingest").addEventListener("click", () => createAndIngest().catch(showError));
    $("refresh-source").addEventListener("click", () => refreshSelectedSource().catch(showError));
    $("generate-report").addEventListener("click", () => generateReport().catch(showError));
    $("fetch-trace").addEventListener("click", () => fetchTrace().catch(showError));
    $("fetch-usage").addEventListener("click", () => fetchUsage().catch(showError));
    $("cleanup-source").addEventListener("click", () => cleanupSource().catch(showError));
    $("load-offline-preview").addEventListener("click", renderOfflinePreview);
    $("source-id").addEventListener("input", () => {
      if (state.sourceId && currentSourceInput() !== state.sourceId) {
        resetSourceTracking("The context identifier changed. Check context status or prepare the context again.");
      }
      updateSnippets();
    });
    ["role-title", "role-context", "business-question", "focus-areas", "base-url"].forEach((id) => $(id).addEventListener("input", updateSnippets));
    document.querySelectorAll(".tab-button").forEach((button) => {
      button.addEventListener("click", () => {
        document.querySelectorAll(".tab-button").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        state.activeSnippet = button.dataset.tab;
        updateSnippets();
      });
    });
    $("copy-snippet").addEventListener("click", () => navigator.clipboard?.writeText($("snippet-code").textContent));
  }

  function showError(error) {
    const message = error.message || "The request could not be completed.";
    setStatus("ingestion-status", message, "error");
    setAlert(message, "error");
    setText("connection-status", message);
    updateGenerateGate();
  }

  async function init() {
    bind();
    renderChecklist();
    resetSourceTracking("No customer context prepared yet.");
    await loadHealth().catch(() => undefined);
    await loadSamples().catch(showError);
    updateGenerateGate();
    updateSnippets();
  }

  init();
})();
