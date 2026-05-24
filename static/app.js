const questionInput = document.querySelector("#questionInput");
const asOfDate = document.querySelector("#asOfDate");
const runBtn = document.querySelector("#runBtn");
const loadSampleBtn = document.querySelector("#loadSampleBtn");
const statusText = document.querySelector("#statusText");
const resultsList = document.querySelector("#resultsList");
const detailPanel = document.querySelector("#detailPanel");
const questionsCount = document.querySelector("#questionsCount");
const reviewCount = document.querySelector("#reviewCount");
const sourceCount = document.querySelector("#sourceCount");
const sidebarEvidenceCount = document.querySelector("#sidebarEvidenceCount");
const freshEvidenceCount = document.querySelector("#freshEvidenceCount");
const staleEvidenceCount = document.querySelector("#staleEvidenceCount");
const outdatedEvidenceCount = document.querySelector("#outdatedEvidenceCount");
const evidenceStatus = document.querySelector("#evidenceStatus");
const evidenceFile = document.querySelector("#evidenceFile");
const uploadEvidenceBtn = document.querySelector("#uploadEvidenceBtn");
const storeEvidenceBtn = document.querySelector("#storeEvidenceBtn");
const evidenceTitle = document.querySelector("#evidenceTitle");
const evidenceType = document.querySelector("#evidenceType");
const evidenceOwner = document.querySelector("#evidenceOwner");
const evidenceReviewed = document.querySelector("#evidenceReviewed");
const evidenceFrameworks = document.querySelector("#evidenceFrameworks");
const evidenceSummary = document.querySelector("#evidenceSummary");
const evidenceSnippets = document.querySelector("#evidenceSnippets");

let answers = [];
let selectedIndex = 0;
let evidenceRecords = [];
let approvals = {};

function today() {
  return new Date().toISOString().slice(0, 10);
}

function setStatus(message, tone = "neutral") {
  statusText.textContent = message;
  statusText.dataset.tone = tone;
}

function truncate(text, limit) {
  if (text.length <= limit) {
    return text;
  }
  return `${text.slice(0, limit - 1).trim()}...`;
}

function confidenceClass(confidence) {
  if (confidence === "high" || confidence === "medium" || confidence === "low") {
    return confidence;
  }
  return "medium";
}

function answerQuality(answer) {
  return window.EvidenceQuality.buildEvidenceQuality(answer);
}

function renderEvidenceStrip(answer) {
  const quality = answerQuality(answer);
  return `
    <div class="evidence-strip" aria-label="${escapeHtml(quality.summary)}">
      ${quality.segments
        .map(
          (segment) => `
            <span class="evidence-segment ${segment.className}">
              <i aria-hidden="true"></i>
              <span>${escapeHtml(segment.label)}</span>
            </span>
          `
        )
        .join("")}
    </div>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function updateMetrics(payload) {
  const uniqueSources = new Set();
  for (const answer of payload.answers || []) {
    for (const citation of answer.citations || []) {
      uniqueSources.add(citation.source_id);
    }
  }
  questionsCount.textContent = payload.summary?.questions_processed || 0;
  reviewCount.textContent = payload.summary?.human_reviews_required || 0;
  sourceCount.textContent = uniqueSources.size;
}

function renderResults() {
  if (!answers.length) {
    resultsList.innerHTML = `
      <div class="results-empty">
        <strong>No drafts yet</strong>
        <p>Load sample questions or add customer questions, then generate drafts to see evidence quality.</p>
      </div>
    `;
    return;
  }

  resultsList.innerHTML = answers
    .map((answer, index) => {
      const active = index === selectedIndex ? " active" : "";
      const quality = answerQuality(answer);
      const review = answer.needs_human_review ? '<span class="meta-chip warning-chip">Human review</span>' : "";
      return `
        <article class="answer-card${active}" role="button" tabindex="0" data-index="${index}">
          <div class="card-top">
            <p class="question-title">${escapeHtml(answer.question)}</p>
            <span class="badge ${confidenceClass(answer.confidence)}">${escapeHtml(answer.confidence)}</span>
          </div>
          ${renderEvidenceStrip(answer)}
          <p class="answer-preview">${escapeHtml(truncate(answer.answer, 190))}</p>
          <div class="meta-row">
            <span class="meta-chip">${escapeHtml(quality.sources.label)}</span>
            <span class="meta-chip">${escapeHtml(quality.freshness.label)}</span>
            ${review}
          </div>
        </article>
      `;
    })
    .join("");

  function selectCard(card) {
    selectedIndex = Number(card.dataset.index);
    renderResults();
    renderDetail();
  }

  for (const card of resultsList.querySelectorAll(".answer-card")) {
    card.addEventListener("click", () => selectCard(card));
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        selectCard(card);
      } else if (event.key === " ") {
        event.preventDefault();
        selectCard(card);
      }
    });
  }
}

function renderDetail() {
  const answer = answers[selectedIndex];
  if (!answer) {
    detailPanel.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon" aria-hidden="true"></div>
        <h3>Select or generate an answer</h3>
        <p>Confidence, citations, and freshness checks will appear here.</p>
      </div>
    `;
    return;
  }

  const quality = answerQuality(answer);
  const warningClass = answer.needs_human_review ? " review-warning" : "";
  detailPanel.innerHTML = `
    <div class="detail-header">
      <div class="detail-kicker">
        <span class="badge ${confidenceClass(answer.confidence)}">${escapeHtml(answer.confidence)} confidence</span>
        <span class="review-state">${escapeHtml(quality.reviewLabel)}</span>
      </div>
      <h3>${escapeHtml(answer.question)}</h3>
      ${answer.template_category ? `<span class="meta-chip">${escapeHtml(answer.template_category)}</span>` : ""}
      ${renderEvidenceStrip(answer)}
      <p>${escapeHtml(answer.confidence_rationale)}</p>
      <div class="button-row detail-actions">
        <button id="exportMarkdownBtn" class="primary-button" type="button">Export Markdown</button>
        <button id="exportCSVBtn" class="ghost-button" type="button">Export CSV</button>
        <button id="exportJSONBtn" class="ghost-button" type="button">Export JSON</button>
      </div>
    </div>
    <div class="answer-body${warningClass}">${escapeHtml(answer.answer)}</div>
    <div class="section-title">Freshness</div>
    <div class="source-list">
      ${renderFreshness(answer.freshness)}
    </div>
    <div class="section-title">Sources</div>
    <div class="source-list">
      ${renderSources(answer.citations)}
    </div>
    ${renderApproval(answer)}
  `;
  document.querySelector("#exportMarkdownBtn").addEventListener("click", () => exportMarkdown(answer));
  document.querySelector("#exportCSVBtn").addEventListener("click", () => exportCSV(answer));
  document.querySelector("#exportJSONBtn").addEventListener("click", () => exportStructuredJSON(answer));
  document.querySelector("#approveBtn")?.addEventListener("click", () => setApproval(answer, "approved"));
  document.querySelector("#rejectBtn")?.addEventListener("click", () => setApproval(answer, "rejected"));
  document.querySelector("#resetApprovalBtn")?.addEventListener("click", () => setApproval(answer, "unreviewed"));
}

function renderFreshness(items) {
  const freshnessItems = Array.isArray(items) ? items : [];
  if (!freshnessItems.length) {
    return '<div class="source-item"><p>No matching evidence found.</p></div>';
  }
  return freshnessItems
    .map(
      (item) => `
        <div class="source-item">
          <strong>${escapeHtml(item.source)}</strong>
          <p>Reviewed ${escapeHtml(item.last_reviewed)}. Evidence age is ${escapeHtml(item.age_days)} days.</p>
          <span class="source-foot">Status: ${escapeHtml(item.status)}</span>
        </div>
      `
    )
    .join("");
}

function renderSources(citations) {
  const citationItems = Array.isArray(citations) ? citations : [];
  if (!citationItems.length) {
    return '<div class="source-item"><p>No citations available. Do not send an answer without review.</p></div>';
  }
  return citationItems
    .map(
      (source) => `
        <div class="source-item">
          <strong>${escapeHtml(source.citation)} ${escapeHtml(source.title)}</strong>
          <p>${escapeHtml(source.snippet)}</p>
          <span class="source-foot">${escapeHtml(source.type)} | ${escapeHtml(source.owner)} | ${escapeHtml(source.last_reviewed)}</span>
        </div>
      `
    )
    .join("");
}

function renderApproval(answer) {
  const question = answer.question;
  const app = approvals[question] || { status: "unreviewed", reviewer: "", notes: "", reviewed_at: null };
  const statusLabels = { unreviewed: "Unreviewed", approved: "Approved", rejected: "Rejected" };
  const statusClass = app.status === "unreviewed" ? "meta-chip" : `meta-chip ${app.status}-chip`;
  const reviewerInfo = app.reviewer
    ? `<p class="approval-meta">Reviewed by ${escapeHtml(app.reviewer)}${app.reviewed_at ? " at " + escapeHtml(app.reviewed_at) : ""}</p>`
    : "";
  const notesHtml = app.notes
    ? `<p class="approval-notes">${escapeHtml(app.notes)}</p>`
    : "";
  return `
    <div class="section-title">Review Status</div>
    <div class="approval-section">
      <div class="approval-status">
        <span class="${statusClass}">${statusLabels[app.status] || "Unreviewed"}</span>
        ${reviewerInfo}
      </div>
      ${notesHtml}
      <div class="approval-actions">
        <button id="approveBtn" class="approval-btn approve-btn" type="button">Approve</button>
        <button id="rejectBtn" class="approval-btn reject-btn" type="button">Reject</button>
        <button id="resetApprovalBtn" class="approval-btn reset-btn" type="button">Reset</button>
      </div>
      <div class="approval-form">
        <input id="reviewerName" type="text" placeholder="Reviewer name" value="${escapeHtml(app.reviewer)}">
        <textarea id="reviewerNotes" placeholder="Review notes (optional)">${escapeHtml(app.notes)}</textarea>
      </div>
    </div>
  `;
}

async function setApproval(answer, status) {
  const question = answer.question;
  const reviewer = document.querySelector("#reviewerName")?.value?.trim() || "";
  const notes = document.querySelector("#reviewerNotes")?.value?.trim() || "";
  try {
    const response = await fetch("/api/approval", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, status, reviewer, notes }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Unable to update approval.");
    }
    approvals[question] = payload;
    renderDetail();
    setStatus(`Answer ${status}.`, "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function loadApprovals() {
  try {
    const response = await fetch("/api/approvals");
    const payload = await response.json();
    approvals = payload.approvals || {};
  } catch {
    approvals = {};
  }
}

async function loadSample() {
  setStatus("Loading sample questions...");
  const response = await fetch("/api/sample");
  const payload = await response.json();
  questionInput.value = payload.questions.join("\n");
  setStatus("Sample questions loaded.", "success");
}

async function generateDrafts() {
  const questionText = questionInput.value.trim();
  if (!questionText) {
    setStatus("Add at least one question first.", "error");
    questionInput.focus();
    return;
  }

  runBtn.disabled = true;
  runBtn.textContent = "Generating...";
  setStatus("Retrieving evidence and drafting answers...");

  try {
    const response = await fetch("/api/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question_text: questionText,
        as_of: asOfDate.value || today(),
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Unable to generate drafts.");
    }
    answers = payload.answers;
    selectedIndex = 0;
    updateMetrics(payload);
    await loadApprovals();
    renderResults();
    renderDetail();
    setStatus(`Generated ${payload.summary.questions_processed} draft answers. Outputs were written to outputs/.`, "success");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = "Generate drafts";
  }
}

async function refreshEvidence() {
  const response = await fetch("/api/evidence");
  const payload = await response.json();
  evidenceRecords = payload.evidence || [];
  const counts = { fresh: 0, stale: 0, outdated: 0 };
  for (const record of evidenceRecords) {
    const reviewed = new Date(`${record.last_reviewed}T00:00:00`);
    const ageDays = Math.floor((new Date(asOfDate.value || today()) - reviewed) / 86400000);
    if (ageDays > 365) {
      counts.outdated += 1;
    } else if (ageDays > 180) {
      counts.stale += 1;
    } else {
      counts.fresh += 1;
    }
  }
  evidenceStatus.textContent = `${evidenceRecords.length} stored documents. ${counts.stale + counts.outdated} stale or outdated.`;
  sidebarEvidenceCount.textContent = evidenceRecords.length;
  freshEvidenceCount.textContent = counts.fresh;
  staleEvidenceCount.textContent = counts.stale;
  outdatedEvidenceCount.textContent = counts.outdated;
}

function buildEvidenceRecordFromForm() {
  const snippets = evidenceSnippets.value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  return {
    title: evidenceTitle.value.trim(),
    type: evidenceType.value.trim() || "evidence",
    owner: evidenceOwner.value.trim() || "Unassigned",
    last_reviewed: evidenceReviewed.value || today(),
    frameworks: evidenceFrameworks.value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    control_ids: [],
    summary: evidenceSummary.value.trim() || snippets[0] || evidenceTitle.value.trim(),
    snippets,
  };
}

function clearEvidenceForm() {
  evidenceTitle.value = "";
  evidenceType.value = "";
  evidenceOwner.value = "";
  evidenceReviewed.value = today();
  evidenceFrameworks.value = "";
  evidenceSummary.value = "";
  evidenceSnippets.value = "";
}

async function postEvidence(records) {
  const response = await fetch("/api/evidence", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ records }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Unable to store evidence.");
  }
  evidenceRecords = payload.evidence || [];
  await refreshEvidence();
  return payload.stored;
}

async function storeEvidenceFromForm() {
  try {
    const stored = await postEvidence([buildEvidenceRecordFromForm()]);
    clearEvidenceForm();
    setStatus(`Stored ${stored} evidence document. New drafts will use the updated evidence library.`, "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function uploadEvidenceFile() {
  evidenceFile.click();
}

async function handleEvidenceFile() {
  const file = evidenceFile.files[0];
  if (!file) {
    return;
  }
  try {
    const payload = JSON.parse(await file.text());
    const records = Array.isArray(payload) ? payload : [payload];
    const stored = await postEvidence(records);
    evidenceFile.value = "";
    setStatus(`Uploaded and stored ${stored} evidence document${stored === 1 ? "" : "s"}.`, "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function exportCSV(answer) {
  try {
    const response = await fetch("/api/export/csv", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Unable to export CSV.");
    }

    const blob = new Blob([payload.csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "customer_ready_answer.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setStatus(`Exported CSV to ${payload.path}.`, "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function exportStructuredJSON(answer) {
  try {
    const response = await fetch("/api/export/json", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Unable to export JSON.");
    }

    const blob = new Blob([payload.json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "customer_ready_answer.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setStatus(`Exported structured JSON to ${payload.path}.`, "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function exportMarkdown(answer) {
  try {
    const response = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Unable to export markdown.");
    }

    const blob = new Blob([payload.markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "customer_ready_answer.md";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setStatus(`Exported markdown to ${payload.path}.`, "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

asOfDate.value = today();
evidenceReviewed.value = today();
loadSampleBtn.addEventListener("click", loadSample);
runBtn.addEventListener("click", generateDrafts);
uploadEvidenceBtn.addEventListener("click", uploadEvidenceFile);
storeEvidenceBtn.addEventListener("click", storeEvidenceFromForm);
evidenceFile.addEventListener("change", handleEvidenceFile);
asOfDate.addEventListener("change", refreshEvidence);

refreshEvidence().then(() => loadSample()).then(generateDrafts);
