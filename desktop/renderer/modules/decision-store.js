export function defaultCandidatesStore() {
  return {
    version: 1,
    updated_at: null,
    baseline_run_id: null,
    entries: [],
  };
}

export function normalizeCandidatesStore(store) {
  const fallback = defaultCandidatesStore();
  if (!store || typeof store !== "object") return fallback;
  const entries = Array.isArray(store.entries)
    ? store.entries
        .filter((entry) => entry && entry.run_id)
        .map((entry) => ({
          run_id: String(entry.run_id),
          note: typeof entry.note === "string" ? entry.note : "",
          shortlisted: Boolean(entry.shortlisted),
          created_at: entry.created_at || new Date().toISOString(),
          updated_at: entry.updated_at || new Date().toISOString(),
        }))
    : [];
  return {
    version: 1,
    updated_at: store.updated_at || null,
    baseline_run_id: store.baseline_run_id ? String(store.baseline_run_id) : null,
    entries,
  };
}

export function getCandidateEntries(store) {
  return Array.isArray(store?.entries) ? store.entries : [];
}

export function getCandidateEntry(store, runId) {
  return getCandidateEntries(store).find((entry) => entry.run_id === runId) || null;
}

export function getCandidateEntryResolved(store, runId, findRun) {
  const entry = getCandidateEntry(store, runId);
  if (!entry) return null;
  return {
    ...entry,
    run: findRun(runId),
  };
}

export function getCandidateEntriesResolved(store, findRun) {
  return getCandidateEntries(store)
    .map((entry) => ({ ...entry, run: findRun(entry.run_id) }))
    .sort((left, right) => {
      const leftDate = new Date(left.updated_at || 0).getTime();
      const rightDate = new Date(right.updated_at || 0).getTime();
      return rightDate - leftDate;
    });
}

export function buildMissingCandidateEntry(runId, findRun) {
  return {
    run_id: runId,
    note: "",
    shortlisted: false,
    updated_at: null,
    created_at: null,
    run: findRun(runId),
  };
}

export function isCandidateRun(store, runId) {
  return Boolean(getCandidateEntry(store, runId));
}

export function isShortlistedRun(store, runId) {
  return Boolean(getCandidateEntry(store, runId)?.shortlisted);
}

export function isBaselineRun(store, runId) {
  return store?.baseline_run_id === runId;
}

export function getShortlistRunIds(store, findRun) {
  return getCandidateEntries(store)
    .filter((entry) => entry.shortlisted)
    .map((entry) => entry.run_id)
    .filter((runId) => findRun(runId));
}

export function getDecisionCompareRunIds(store, findRun, uniqueRunIds, maxCandidateCompare) {
  const runIds = [...getShortlistRunIds(store, findRun)];
  if (store?.baseline_run_id && findRun(store.baseline_run_id)) {
    runIds.unshift(store.baseline_run_id);
  }
  return uniqueRunIds(runIds).slice(0, maxCandidateCompare);
}

export function summarizeCandidateState(store, runId) {
  const labels = [];
  if (isBaselineRun(store, runId)) labels.push("baseline");
  if (isShortlistedRun(store, runId)) labels.push("shortlist");
  if (isCandidateRun(store, runId)) labels.push("candidate");
  return labels.length ? labels.join(" · ") : "not tracked";
}
