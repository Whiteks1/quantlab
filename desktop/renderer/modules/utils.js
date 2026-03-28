export function titleCase(value) {
  return String(value || "").replace(/[_-]+/g, " ").replace(/\b\w/g, (match) => match.toUpperCase());
}

export function shortCommit(value) {
  return value ? String(value).slice(0, 7) : "";
}

export function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatPercent(value) {
  return typeof value === "number" && !Number.isNaN(value) ? `${(value * 100).toFixed(2)}%` : "-";
}

export function formatNumber(value) {
  return typeof value === "number" && !Number.isNaN(value) ? value.toFixed(2) : "-";
}

export function formatCount(value) {
  return typeof value === "number" && !Number.isNaN(value) ? value.toFixed(0) : "-";
}

export function formatBytes(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "-";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function toneClass(value, higherIsBetter) {
  if (typeof value !== "number" || Number.isNaN(value)) return "";
  const good = higherIsBetter ? value > 0 : value > -0.15;
  const bad = higherIsBetter ? value < 0 : value < -0.3;
  if (good) return "tone-positive";
  if (bad) return "tone-negative";
  return "";
}

export function metricValue(value) {
  return typeof value === "number" && !Number.isNaN(value) ? value : Number.NEGATIVE_INFINITY;
}

export function stripWrappingQuotes(value) {
  return String(value || "").replace(/^["']|["']$/g, "");
}

export function escapeRegex(value) {
  return String(value || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function formatLogPreview(text, maxLogPreviewChars) {
  const value = String(text || "");
  if (!value) return "";
  return value.length > maxLogPreviewChars
    ? `${value.slice(-maxLogPreviewChars)}\n\n[truncated to latest ${maxLogPreviewChars} chars]`
    : value;
}

export function runtimeChip(label, value, tone) {
  return `<div class="runtime-chip ${escapeHtml(tone)}"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(value)}</span></div>`;
}

export function buildRunArtifactHref(runPath, fileName) {
  const base = toOutputsHref(runPath);
  return base ? `${base}/${fileName}` : "";
}

export function toOutputsHref(absolutePath) {
  const match = String(absolutePath || "").match(/[\\/](outputs[\\/].*)$/i);
  return match ? `/${match[1].replace(/\\/g, "/")}` : "";
}

export function absoluteUrl(serverUrl, relativeOrUrl) {
  if (!relativeOrUrl) return "";
  if (/^https?:\/\//i.test(relativeOrUrl)) return relativeOrUrl;
  return serverUrl ? `${serverUrl.replace(/\/$/, "")}${relativeOrUrl}` : "";
}

export function closeMetric(left, right) {
  if (typeof left !== "number" || typeof right !== "number") return false;
  return Math.abs(left - right) < 0.000001;
}

export function selectPrimaryResult(run, report) {
  const results = Array.isArray(report?.results) ? report.results.filter(Boolean) : [];
  if (!results.length) return null;
  const exact = results.find((result) =>
    closeMetric(result.total_return, run?.total_return) &&
    closeMetric(result.sharpe_simple, run?.sharpe_simple) &&
    closeMetric(result.max_drawdown, run?.max_drawdown),
  );
  if (exact) return exact;
  return results.reduce((best, result) => {
    if (!best) return result;
    return metricValue(result.sharpe_simple) > metricValue(best.sharpe_simple) ? result : best;
  }, null);
}

export function selectTopResults(results, limit = 4) {
  if (!Array.isArray(results)) return [];
  return [...results]
    .filter(Boolean)
    .sort((left, right) => metricValue(right.sharpe_simple) - metricValue(left.sharpe_simple))
    .slice(0, limit);
}

export function rankRunsByMetric(runs, metric) {
  const sorter = metric === "max_drawdown"
    ? (left, right) => metricValue(right.max_drawdown) - metricValue(left.max_drawdown)
    : (left, right) => metricValue(right[metric]) - metricValue(left[metric]);
  return [...runs].sort(sorter);
}

export function formatMetricForDisplay(value, metric) {
  if (metric === "trades") return formatCount(value);
  if (metric === "max_drawdown" || metric === "total_return" || metric === "win_rate_trades" || metric === "exposure") {
    return formatPercent(value);
  }
  return formatNumber(value);
}

export function collectConfigDeltas(runs, detailMap) {
  const valueMap = new Map();
  runs.forEach((run) => {
    const detail = detailMap?.[run.run_id];
    const config = detail?.report?.config_resolved;
    if (!config || typeof config !== "object") return;
    Object.entries(config).forEach(([key, value]) => {
      const current = valueMap.get(key) || new Set();
      current.add(stringifyValue(value));
      valueMap.set(key, current);
    });
  });
  return [...valueMap.entries()]
    .filter(([, values]) => values.size > 1)
    .map(([key, values]) => [key, [...values].slice(0, 4)])
    .slice(0, 12);
}

export function summarizeObjectEntries(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];
  return Object.entries(value).map(([key, item]) => [titleCase(key.replace(/_/g, " ")), stringifyValue(item)]);
}

export function stringifyValue(value) {
  if (Array.isArray(value)) return value.map((item) => stringifyValue(item)).join(", ");
  if (value && typeof value === "object") return JSON.stringify(value);
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
}

export function uniqueRunIds(runIds) {
  return [...new Set((runIds || []).filter(Boolean))];
}

