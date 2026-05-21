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
    resultsList.innerHTML = "";
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
      ${renderEvidenceStrip(answer)}
      <p>${escapeHtml(answer.confidence_rationale)}</p>
      <div class="button-row detail-actions">
        <button id="exportMarkdownBtn" class="primary-button" type="button">Export Markdown</button>
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
  `;
  document.querySelector("#exportMarkdownBtn").addEventListener("click", () => exportMarkdown(answer));
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
