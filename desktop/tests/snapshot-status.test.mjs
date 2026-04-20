import test from "node:test";
import assert from "node:assert/strict";

import { describeSnapshotRefresh } from "../shared/snapshot-status.mjs";

const ISO_TIME = "2026-04-10T14:00:00.000Z";

test("ok snapshots render as live", () => {
  const result = describeSnapshotRefresh({
    status: "ok",
    refreshPaused: false,
    lastSuccessAt: ISO_TIME,
  });

  assert.equal(result.label, "Live");
  assert.equal(result.tone, "tone-positive");
  assert.notEqual(result.lastSuccessAt, "Never");
});

test("degraded snapshots stay warning-toned and do not fall back to waiting", () => {
  const result = describeSnapshotRefresh({
    status: "degraded",
    refreshPaused: false,
    lastSuccessAt: ISO_TIME,
  });

  assert.equal(result.label, "Degraded");
  assert.equal(result.tone, "tone-warning");
});

test("error snapshots remain negative and explicitly unavailable", () => {
  const result = describeSnapshotRefresh({
    status: "error",
    refreshPaused: false,
    lastSuccessAt: ISO_TIME,
  });

  assert.equal(result.label, "Unavailable");
  assert.equal(result.tone, "tone-negative");
});

test("idle snapshots remain waiting", () => {
  const result = describeSnapshotRefresh({
    status: "idle",
    refreshPaused: false,
    lastSuccessAt: null,
  });

  assert.equal(result.label, "Waiting");
  assert.equal(result.tone, "tone-warning");
  assert.equal(result.lastSuccessAt, "Never");
});
