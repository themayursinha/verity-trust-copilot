import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";

const require = createRequire(import.meta.url);
const EvidenceQuality = require("./evidence_quality.js");

test("buildEvidenceQuality returns strong segments for high confidence with multiple fresh sources", () => {
  const quality = EvidenceQuality.buildEvidenceQuality({
    confidence: "high",
    citations: [{ source_id: "a" }, { source_id: "b" }],
    freshness: [
      { status: "fresh", source: "a" },
      { status: "fresh", source: "b" },
    ],
    needs_human_review: false,
  });

  assert.equal(quality.confidence.label, "High confidence");
  assert.equal(quality.confidence.className, "quality-good");
  assert.equal(quality.sources.label, "2 sources");
  assert.equal(quality.sources.className, "quality-good");
  assert.equal(quality.freshness.label, "Fresh evidence");
  assert.equal(quality.freshness.className, "quality-good");
  assert.equal(quality.summary, "High confidence · 2 sources · Fresh evidence");
});

test("buildEvidenceQuality marks one stale source as caution", () => {
  const quality = EvidenceQuality.buildEvidenceQuality({
    confidence: "medium",
    citations: [{ source_id: "access-control" }],
    freshness: [{ status: "stale", source: "access-control" }],
    needs_human_review: false,
  });

  assert.equal(quality.confidence.label, "Medium confidence");
  assert.equal(quality.confidence.className, "quality-caution");
  assert.equal(quality.sources.label, "1 source");
  assert.equal(quality.sources.className, "quality-caution");
  assert.equal(quality.freshness.label, "Stale evidence");
  assert.equal(quality.freshness.className, "quality-caution");
});

test("buildEvidenceQuality marks low confidence with no evidence as danger", () => {
  const quality = EvidenceQuality.buildEvidenceQuality({
    confidence: "low",
    citations: [],
    freshness: [],
    needs_human_review: true,
  });

  assert.equal(quality.confidence.label, "Low confidence");
  assert.equal(quality.confidence.className, "quality-danger");
  assert.equal(quality.sources.label, "No sources");
  assert.equal(quality.sources.className, "quality-danger");
  assert.equal(quality.freshness.label, "No evidence");
  assert.equal(quality.freshness.className, "quality-danger");
  assert.equal(quality.reviewLabel, "Human review required");
});

test("buildEvidenceQuality treats outdated freshness as danger even with citations", () => {
  const quality = EvidenceQuality.buildEvidenceQuality({
    confidence: "medium",
    citations: [{ source_id: "old-policy" }, { source_id: "new-policy" }],
    freshness: [
      { status: "outdated", source: "old-policy" },
      { status: "fresh", source: "new-policy" },
    ],
    needs_human_review: false,
  });

  assert.equal(quality.sources.label, "2 sources");
  assert.equal(quality.freshness.label, "Outdated evidence");
  assert.equal(quality.freshness.className, "quality-danger");
});


test("editable list rendering does not embed raw JSON in edit attributes", () => {
  const policySource = readFileSync(new URL("./policies.js", import.meta.url), "utf8");
  const pentestSource = readFileSync(new URL("./pentests.js", import.meta.url), "utf8");

  assert.doesNotMatch(policySource, /data-edit='\$\{JSON\.stringify/);
  assert.doesNotMatch(policySource, /JSON\.stringify\(p\)/);
  assert.match(policySource, /policiesById = new Map/);
  assert.match(policySource, /data-edit-id/);

  assert.doesNotMatch(pentestSource, /data-edit=.*JSON\.stringify/);
  assert.doesNotMatch(pentestSource, /JSON\.stringify\(p\)/);
  assert.match(pentestSource, /pentestsById = new Map/);
  assert.match(pentestSource, /data-edit-id/);
});

test("mock Vanta UI does not request API keys", () => {
  const source = readFileSync(new URL("./dashboard.js", import.meta.url), "utf8");

  assert.doesNotMatch(source, /vantaApiKey/);
  assert.doesNotMatch(source, /Vanta API Key/);
  assert.match(source, /Mock Vanta import/);
});
