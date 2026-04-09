import { escapeHtml } from "./utils.js";

function toDataAttributeName(key) {
  return String(key || "")
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/_/g, "-")
    .toLowerCase();
}

export function renderEmptyState(text) {
  return `<div class="empty-state">${escapeHtml(text)}</div>`;
}

export function renderActionButton({ label, dataset = {}, className = "ghost-btn", type = "button", disabled = false }) {
  const dataAttributes = Object.entries(dataset)
    .filter(([, value]) => value !== null && value !== undefined && value !== false)
    .map(([key, value]) => ` data-${toDataAttributeName(key)}="${escapeHtml(value === true ? "true" : String(value))}"`)
    .join("");
  return `<button class="${escapeHtml(className)}" type="${escapeHtml(type)}"${dataAttributes}${disabled ? " disabled" : ""}>${escapeHtml(label)}</button>`;
}

export function renderActionRow(actions, className = "workflow-actions") {
  const visibleActions = (actions || []).filter(Boolean);
  if (!visibleActions.length) return "";
  return `<div class="${escapeHtml(className)}">${visibleActions.join("")}</div>`;
}

export function renderMetricList(entries, { compact = false, className = "" } = {}) {
  const classes = ["metric-list", compact ? "compact" : "", className].filter(Boolean).join(" ");
  return `
    <dl class="${escapeHtml(classes)}">
      ${(entries || []).map((entry) => `
        <div class="${escapeHtml(entry?.tone || "")}">
          <dt>${escapeHtml(entry?.label || "-")}</dt>
          <dd>${escapeHtml(entry?.value || "-")}</dd>
        </div>
      `).join("")}
    </dl>
  `;
}
