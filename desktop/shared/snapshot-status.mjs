function formatDateTime(value) {
  if (!value) return "Never";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Never";
  return date.toISOString();
}

export function describeSnapshotRefresh(snapshotStatus) {
  if (snapshotStatus?.status === "ok") {
    return {
      label: snapshotStatus.refreshPaused ? "Paused" : "Live",
      tone: snapshotStatus.refreshPaused ? "tone-warning" : "tone-positive",
      lastSuccessAt: snapshotStatus.lastSuccessAt ? formatDateTime(snapshotStatus.lastSuccessAt) : "Never",
    };
  }
  if (snapshotStatus?.status === "degraded") {
    return {
      label: snapshotStatus.refreshPaused ? "Review required" : "Degraded",
      tone: "tone-warning",
      lastSuccessAt: snapshotStatus.lastSuccessAt ? formatDateTime(snapshotStatus.lastSuccessAt) : "Never",
    };
  }
  if (snapshotStatus?.status === "error") {
    return {
      label: snapshotStatus.refreshPaused ? "Review required" : "Unavailable",
      tone: "tone-negative",
      lastSuccessAt: snapshotStatus.lastSuccessAt ? formatDateTime(snapshotStatus.lastSuccessAt) : "Never",
    };
  }
  return {
    label: "Waiting",
    tone: "tone-warning",
    lastSuccessAt: snapshotStatus?.lastSuccessAt ? formatDateTime(snapshotStatus.lastSuccessAt) : "Never",
  };
}
