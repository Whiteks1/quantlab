export function defaultSweepDecisionStore() {
  return {
    version: 1,
    updated_at: null,
    baseline_entry_id: null,
    entries: [],
  };
}

export function normalizeSweepDecisionStore(store) {
  const fallback = defaultSweepDecisionStore();
  if (!store || typeof store !== "object") return fallback;
  const entries = Array.isArray(store.entries)
    ? store.entries
        .filter((entry) => entry && entry.entry_id && entry.sweep_run_id)
        .map((entry) => ({
          entry_id: String(entry.entry_id),
          sweep_run_id: String(entry.sweep_run_id),
          source: typeof entry.source === "string" ? entry.source : "leaderboard",
          row_index: Number.isFinite(Number(entry.row_index)) ? Number(entry.row_index) : 0,
          note: typeof entry.note === "string" ? entry.note : "",
          shortlisted: Boolean(entry.shortlisted),
          config_path: typeof entry.config_path === "string" ? entry.config_path : "",
          row_snapshot: entry.row_snapshot && typeof entry.row_snapshot === "object" ? entry.row_snapshot : null,
          created_at: entry.created_at || new Date().toISOString(),
          updated_at: entry.updated_at || new Date().toISOString(),
        }))
    : [];
  return {
    version: 1,
    updated_at: store.updated_at || null,
    baseline_entry_id: store.baseline_entry_id ? String(store.baseline_entry_id) : null,
    entries,
  };
}

export function getSweepDecisionEntries(store) {
  return Array.isArray(store?.entries) ? store.entries : [];
}

export function getSweepDecisionEntry(store, entryId) {
  return getSweepDecisionEntries(store).find((entry) => entry.entry_id === entryId) || null;
}

export function getSweepDecisionEntriesResolved(store, findLiveRow) {
  return getSweepDecisionEntries(store)
    .map((entry) => {
      const liveRow = findLiveRow(entry.entry_id);
      return {
        ...entry,
        row: liveRow || entry.row_snapshot || null,
        is_missing: !liveRow && !entry.row_snapshot,
      };
    })
    .sort((left, right) => {
      const leftDate = new Date(left.updated_at || 0).getTime();
      const rightDate = new Date(right.updated_at || 0).getTime();
      return rightDate - leftDate;
    });
}

export function isTrackedSweepEntry(store, entryId) {
  return Boolean(getSweepDecisionEntry(store, entryId));
}

export function isShortlistedSweepEntry(store, entryId) {
  return Boolean(getSweepDecisionEntry(store, entryId)?.shortlisted);
}

export function isBaselineSweepEntry(store, entryId) {
  return store?.baseline_entry_id === entryId;
}

export function getSweepDecisionCompareEntries(store, findLiveRow, maxEntries = 4) {
  const entries = getSweepDecisionEntriesResolved(store, findLiveRow);
  const shortlisted = entries.filter((entry) => entry.shortlisted);
  const preferred = shortlisted.length ? shortlisted : entries;
  const withBaseline = [];
  if (store?.baseline_entry_id) {
    const baseline = preferred.find((entry) => entry.entry_id === store.baseline_entry_id)
      || entries.find((entry) => entry.entry_id === store.baseline_entry_id);
    if (baseline) withBaseline.push(baseline);
  }
  preferred.forEach((entry) => {
    if (!withBaseline.some((current) => current.entry_id === entry.entry_id)) {
      withBaseline.push(entry);
    }
  });
  return withBaseline.slice(0, maxEntries);
}

export function summarizeSweepDecisionState(store, entryId) {
  const labels = [];
  if (isBaselineSweepEntry(store, entryId)) labels.push("baseline");
  if (isShortlistedSweepEntry(store, entryId)) labels.push("shortlist");
  if (isTrackedSweepEntry(store, entryId)) labels.push("tracked");
  return labels.length ? labels.join(" · ") : "untracked";
}
