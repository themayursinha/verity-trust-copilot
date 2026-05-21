(function attachEvidenceQuality(globalScope) {
  function normalizeList(value) {
    return Array.isArray(value) ? value : [];
  }

  function confidenceSegment(answer) {
    const confidence = String(answer?.confidence || "medium").toLowerCase();
    if (confidence === "high") {
      return { key: "confidence", label: "High confidence", className: "quality-good" };
    }
    if (confidence === "low") {
      return { key: "confidence", label: "Low confidence", className: "quality-danger" };
    }
    return { key: "confidence", label: "Medium confidence", className: "quality-caution" };
  }

  function sourcesSegment(answer) {
    const count = normalizeList(answer?.citations).length;
    if (count === 0) {
      return { key: "sources", label: "No sources", className: "quality-danger" };
    }
    if (count === 1) {
      return { key: "sources", label: "1 source", className: "quality-caution" };
    }
    return { key: "sources", label: `${count} sources`, className: "quality-good" };
  }

  function freshnessSegment(answer) {
    const freshness = normalizeList(answer?.freshness);
    const statuses = freshness.map((item) => String(item?.status || "").toLowerCase());
    if (!statuses.length) {
      return { key: "freshness", label: "No evidence", className: "quality-danger" };
    }
    if (statuses.includes("outdated")) {
      return { key: "freshness", label: "Outdated evidence", className: "quality-danger" };
    }
    if (statuses.includes("stale")) {
      return { key: "freshness", label: "Stale evidence", className: "quality-caution" };
    }
    return { key: "freshness", label: "Fresh evidence", className: "quality-good" };
  }

  function buildEvidenceQuality(answer) {
    const confidence = confidenceSegment(answer);
    const sources = sourcesSegment(answer);
    const freshness = freshnessSegment(answer);
    return {
      confidence,
      sources,
      freshness,
      segments: [confidence, sources, freshness],
      summary: `${confidence.label} · ${sources.label} · ${freshness.label}`,
      reviewLabel: answer?.needs_human_review ? "Human review required" : "Review optional",
    };
  }

  const api = { buildEvidenceQuality };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }

  globalScope.EvidenceQuality = api;
})(typeof window !== "undefined" ? window : globalThis);
