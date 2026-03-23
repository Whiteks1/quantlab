const CONFIG = {
    registryPath: "/outputs/runs/runs_index.json",
    refreshInterval: 30000,
    detailArtifacts: ["run_report.json", "report.json"],
};

const state = {
    runs: [],
    filteredRuns: [],
    generatedAt: null,
    nRuns: 0,
    sortField: "created_at",
    sortDir: "desc",
    filterMode: "all",
    searchQuery: "",
    isLoading: false,
    currentRunId: null,
    detailCache: new Map(),
};

const elements = {
    runsBody: document.getElementById("runs-body"),
    totalRuns: document.getElementById("stats-total-runs"),
    activeSessions: document.getElementById("stats-active-sessions"),
    bestSharpe: document.getElementById("stats-best-sharpe"),
    bestRun: document.getElementById("stats-best-run"),
    avgReturn: document.getElementById("stats-avg-return"),
    drawdownFloor: document.getElementById("stats-drawdown-floor"),
    generatedAt: document.getElementById("stats-generated-at"),
    searchInput: document.getElementById("run-search"),
    modeFilter: document.getElementById("filter-mode"),
    refreshBtn: document.getElementById("refresh-data"),
    breadcrumb: document.getElementById("breadcrumb"),
    views: {
        runs: document.getElementById("run-index-view"),
        detail: document.getElementById("run-detail-view"),
    },
    navItems: {
        runs: document.getElementById("nav-runs"),
        compare: document.getElementById("nav-compare"),
    },
    detailBody: document.getElementById("detail-body"),
    registryStatus: document.getElementById("registry-status"),
    registryDate: document.getElementById("registry-date"),
    registryDot: document.getElementById("registry-dot"),
    heroSummary: document.getElementById("hero-summary"),
    heroBestRun: document.getElementById("hero-best-run"),
    heroBestMeta: document.getElementById("hero-best-meta"),
    heroRootPill: document.getElementById("hero-root-pill"),
    heroRegistryPill: document.getElementById("hero-registry-pill"),
    heroModeMeta: document.getElementById("hero-mode-meta"),
    modeStrip: document.getElementById("mode-strip"),
    modePills: document.getElementById("mode-pills"),
    tableSummary: document.getElementById("table-summary"),
    toastContainer: document.getElementById("toast-container"),
};

document.addEventListener("DOMContentLoaded", () => {
    elements.refreshBtn.addEventListener("click", () => fetchRegistry(true));
    elements.searchInput.addEventListener("input", (event) => {
        state.searchQuery = event.target.value.trim().toLowerCase();
        applyFilters();
    });
    elements.modeFilter.addEventListener("change", (event) => {
        state.filterMode = event.target.value;
        syncModePills();
        applyFilters();
    });
    document.querySelectorAll("th[data-sort]").forEach((header) => {
        header.addEventListener("click", () => {
            state.sortDir = state.sortField === header.dataset.sort && state.sortDir === "desc" ? "asc" : "desc";
            state.sortField = header.dataset.sort;
            applyFilters();
        });
    });
    elements.modePills.addEventListener("click", (event) => {
        const button = event.target.closest("[data-mode]");
        if (!button) {
            return;
        }
        state.filterMode = button.dataset.mode;
        elements.modeFilter.value = state.filterMode;
        syncModePills();
        applyFilters();
    });
    window.addEventListener("hashchange", route);
    fetchRegistry();
    route();
    window.setInterval(() => fetchRegistry(false, true), CONFIG.refreshInterval);
});

async function fetchRegistry(showToast = false, silent = false) {
    state.isLoading = true;
    renderTable();
    setRegistryState("syncing");

    try {
        const response = await fetch(`${CONFIG.registryPath}?t=${Date.now()}`);
        if (!response.ok) {
            throw new Error(`Artifact not found: ${response.status}`);
        }
        const payload = await response.json();
        state.runs = (payload.runs || []).map(normalizeRun);
        state.generatedAt = payload.generated_at || null;
        state.nRuns = Number.isFinite(payload.n_runs) ? payload.n_runs : state.runs.length;
        populateModeFilter();
        applyFilters();
        setRegistryState("ready");
        if (showToast) {
            notify("Registry synchronized", "success");
        } else if (!silent) {
            notify("Registry loaded", "info");
        }
        if (state.currentRunId) {
            await loadRunDetail(state.currentRunId, true);
        }
    } catch (error) {
        state.runs = [];
        state.filteredRuns = [];
        state.nRuns = 0;
        updateDashboard();
        renderTable();
        setRegistryState("error", error.message);
        notify(`Registry fetch failed: ${error.message}`, "error");
    } finally {
        state.isLoading = false;
        renderTable();
    }
}

function normalizeRun(run) {
    return {
        ...run,
        total_return: toNumber(run.total_return),
        sharpe_simple: toNumber(run.sharpe_simple),
        max_drawdown: toNumber(run.max_drawdown),
        trades: toNumber(run.trades),
        path: normalizePath(run.path || `outputs/runs/${run.run_id || ""}`),
    };
}

function applyFilters() {
    let runs = [...state.runs];
    if (state.searchQuery) {
        runs = runs.filter((run) => [run.run_id, run.mode, run.ticker, run.git_commit, run.start, run.end]
            .filter(Boolean)
            .some((value) => String(value).toLowerCase().includes(state.searchQuery)));
    }
    if (state.filterMode !== "all") {
        runs = runs.filter((run) => run.mode === state.filterMode);
    }
    runs.sort((left, right) => compareRuns(left, right));
    state.filteredRuns = runs;
    updateDashboard();
    renderTable();
}

function compareRuns(left, right) {
    const a = left[state.sortField];
    const b = right[state.sortField];
    if (a == null) {
        return 1;
    }
    if (b == null) {
        return -1;
    }
    const dir = state.sortDir === "asc" ? 1 : -1;
    if (state.sortField === "created_at") {
        return (new Date(a).getTime() - new Date(b).getTime()) * dir;
    }
    if (typeof a === "number" && typeof b === "number") {
        return (a - b) * dir;
    }
    return String(a).localeCompare(String(b)) * dir;
}

function populateModeFilter() {
    const modes = ["all", ...new Set(state.runs.map((run) => run.mode).filter(Boolean))];
    elements.modeFilter.innerHTML = modes.map((mode) => `<option value="${mode}">${mode === "all" ? "All Modes" : titleCase(mode)}</option>`).join("");
    elements.modePills.innerHTML = modes.map((mode) => `<button class="pill-button${mode === state.filterMode ? " active" : ""}" type="button" data-mode="${mode}">${mode === "all" ? "All" : titleCase(mode)}</button>`).join("");
    elements.modeFilter.value = state.filterMode;
}

function syncModePills() {
    elements.modePills.querySelectorAll("[data-mode]").forEach((button) => {
        button.classList.toggle("active", button.dataset.mode === state.filterMode);
    });
}

function updateDashboard() {
    const topRun = [...state.runs].filter((run) => typeof run.sharpe_simple === "number").sort((a, b) => b.sharpe_simple - a.sharpe_simple)[0];
    const avgReturn = average(state.runs.map((run) => run.total_return).filter(isNumber));
    const minDrawdown = state.runs.map((run) => run.max_drawdown).filter(isNumber).reduce((min, value) => Math.min(min, value), Infinity);
    const activeRuns = state.runs.filter((run) => run.created_at && Date.now() - new Date(run.created_at).getTime() <= 86400000).length;
    const modeCounts = state.runs.reduce((acc, run) => ({ ...acc, [run.mode || "unknown"]: (acc[run.mode || "unknown"] || 0) + 1 }), {});

    elements.totalRuns.textContent = String(state.nRuns);
    elements.activeSessions.textContent = String(activeRuns);
    elements.bestSharpe.textContent = topRun ? formatNumber(topRun.sharpe_simple) : "-";
    elements.bestRun.textContent = topRun ? `${topRun.run_id} · ${titleCase(topRun.mode)}` : "Awaiting best run";
    elements.avgReturn.textContent = formatPercent(avgReturn);
    elements.drawdownFloor.textContent = `Drawdown floor: ${isFinite(minDrawdown) ? formatPercent(minDrawdown) : "-"}`;
    elements.generatedAt.textContent = `Artifact generated: ${formatDateTime(state.generatedAt)}`;
    elements.heroSummary.textContent = state.runs.length ? `${state.filteredRuns.length} visible of ${state.nRuns} indexed runs. Drill into canonical artifacts without leaving the dashboard.` : "No indexed runs available yet.";
    elements.heroBestRun.textContent = topRun ? topRun.run_id : "No best run yet";
    elements.heroBestMeta.textContent = topRun ? `${titleCase(topRun.mode)} · Sharpe ${formatNumber(topRun.sharpe_simple)} · Return ${formatPercent(topRun.total_return)}` : "Waiting for usable metrics";
    elements.heroModeMeta.textContent = state.runs.length ? `${Object.keys(modeCounts).length} active modes in the current registry` : "Mode distribution appears after sync";
    elements.heroRootPill.textContent = "Source: outputs/runs";
    elements.tableSummary.textContent = state.runs.length ? `Sorted by ${titleCase(state.sortField.replace(/_/g, " "))} (${state.sortDir}). ${state.filteredRuns.length} rows visible.` : "Registry rows will appear here after the first successful sync.";
    elements.modeStrip.innerHTML = Object.entries(modeCounts).sort((a, b) => b[1] - a[1]).map(([mode, count]) => `<div class="mode-chip"><span>${titleCase(mode)}</span><span class="mode-chip-bar" style="width:${Math.max(18, count * 28)}px"></span><strong>${count}</strong></div>`).join("") || `<span class="mode-chip muted">No active modes</span>`;
}

function renderTable() {
    if (state.isLoading && !state.runs.length) {
        elements.runsBody.innerHTML = `<tr><td colspan="9" class="loading-state"><div class="spinner"></div>Accessing QuantLab artifacts...</td></tr>`;
        return;
    }
    if (!state.filteredRuns.length) {
        elements.runsBody.innerHTML = `<tr><td colspan="9" class="loading-state"><div class="empty-panel"><strong>No runs matched the current filters.</strong><span>Try another search or resync the registry.</span></div></td></tr>`;
        return;
    }
    elements.runsBody.innerHTML = state.filteredRuns.map((run) => `
        <tr>
            <td><div class="run-primary"><span class="font-mono">${escapeHtml(run.run_id || "unnamed")}</span><span class="mini-meta">${escapeHtml(shortCommit(run.git_commit) || "no-commit")}</span></div></td>
            <td><span class="badge ${modeBadge(run.mode)}">${escapeHtml(run.mode || "unknown")}</span></td>
            <td>${escapeHtml(run.ticker || "N/A")}</td>
            <td class="${tone(run.total_return, true)}">${formatPercent(run.total_return)}</td>
            <td>${formatNumber(run.sharpe_simple)}</td>
            <td class="${tone(run.max_drawdown, false)}">${formatPercent(run.max_drawdown)}</td>
            <td>${formatCount(run.trades)}</td>
            <td class="text-secondary">${formatDateTime(run.created_at)}</td>
            <td><div class="table-actions"><a class="btn-icon" href="#/run/${encodeURIComponent(run.run_id)}" title="View details">◉</a><a class="btn-icon" href="${preferredReportHref(run)}" target="_blank" rel="noreferrer" title="Open readable report">↗</a></div></td>
        </tr>
    `).join("");
}

function route() {
    const hash = window.location.hash || "#/";
    Object.values(elements.views).forEach((view) => view.classList.remove("active"));
    Object.values(elements.navItems).forEach((item) => item.classList.remove("active"));
    if (hash.startsWith("#/run/")) {
        state.currentRunId = decodeURIComponent(hash.split("/")[2] || "");
        elements.views.detail.classList.add("active");
        elements.navItems.runs.classList.add("active");
        elements.breadcrumb.textContent = `Run Detail · ${state.currentRunId}`;
        loadRunDetail(state.currentRunId);
        return;
    }
    state.currentRunId = null;
    elements.views.runs.classList.add("active");
    elements.navItems.runs.classList.add("active");
    elements.breadcrumb.textContent = "Run Registry";
}

async function loadRunDetail(runId, silent = false) {
    const run = state.runs.find((entry) => entry.run_id === runId);
    if (!run) {
        elements.detailBody.innerHTML = `<div class="detail-empty"><a href="#/" class="back-link">Back to registry</a><h2>Run not found</h2><p>${escapeHtml(runId)} is not present in the current registry snapshot.</p></div>`;
        return;
    }
    if (state.detailCache.has(runId)) {
        renderDetail(run, state.detailCache.get(runId));
        return;
    }
    if (!silent) {
        elements.detailBody.innerHTML = `<div class="loading-state detail-loading"><div class="spinner"></div>Loading canonical artifacts for ${escapeHtml(runId)}...</div>`;
    }
    let detail = { report: null, reportUrl: null };
    for (const artifact of CONFIG.detailArtifacts) {
        const url = `${run.path}/${artifact}`;
        try {
            const response = await fetch(url);
            if (!response.ok) {
                continue;
            }
            detail = { report: await response.json(), reportUrl: url };
            break;
        } catch (_error) {
            // Try next candidate.
        }
    }
    state.detailCache.set(runId, detail);
    renderDetail(run, detail);
}

function renderDetail(run, detail) {
    const report = detail.report;
    const primary = report?.results?.[0] || report?.oos_leaderboard?.[0] || report?.summary?.[0] || report?.summary || {};
    const artifacts = Array.isArray(report?.artifacts) ? report.artifacts : [];
    const rows = report?.results?.length ? report.results.slice(0, 6) : report?.oos_leaderboard?.length ? report.oos_leaderboard.slice(0, 6) : report?.summary?.length ? report.summary.slice(0, 6) : [];
    const columns = rows[0] ? Object.keys(rows[0]).slice(0, 8) : [];

    elements.detailBody.innerHTML = `
        <div class="detail-shell">
            <div class="detail-topbar">
                <a href="#/" class="back-link">Back to registry</a>
                <div class="detail-links">${detail.reportUrl ? `<a href="${detail.reportUrl}" target="_blank" rel="noreferrer" class="text-link">Raw JSON</a>` : ""}</div>
            </div>
            <section class="detail-hero">
                <div>
                    <div class="hero-kicker"><span class="badge ${modeBadge(run.mode)}">${escapeHtml(run.mode || "unknown")}</span><span class="pill">${escapeHtml(run.ticker || "Ticker unavailable")}</span></div>
                    <h2>${escapeHtml(run.run_id)}</h2>
                    <p>${escapeHtml(report ? "Canonical artifact loaded from the run directory." : "No readable report artifact was found. Showing registry-level metrics only.")}</p>
                </div>
                <div class="detail-hero-meta">
                    <div><span>Created</span><strong>${formatDateTime(run.created_at)}</strong></div>
                    <div><span>Window</span><strong>${escapeHtml(run.start || "?")} → ${escapeHtml(run.end || "?")}</strong></div>
                    <div><span>Commit</span><strong class="font-mono">${escapeHtml(shortCommit(run.git_commit) || "N/A")}</strong></div>
                </div>
            </section>
            <section class="metric-grid">
                ${metricCard("Return", formatPercent(primary.total_return ?? run.total_return), tone(primary.total_return ?? run.total_return, true))}
                ${metricCard("Sharpe", formatNumber(primary.sharpe_simple ?? run.sharpe_simple), "tone-positive")}
                ${metricCard("Drawdown", formatPercent(primary.max_drawdown ?? run.max_drawdown), tone(primary.max_drawdown ?? run.max_drawdown, false))}
                ${metricCard("Trades", formatCount(primary.trades ?? primary.trade_trades ?? run.trades), "tone-positive")}
                ${metricCard("Win Rate", formatPercent(primary.win_rate ?? primary.win_rate_trades), "tone-positive")}
                ${metricCard("Profit Factor", formatNumber(primary.profit_factor), "tone-positive")}
            </section>
            <section class="detail-grid">
                <article class="detail-panel glass">
                    <div class="panel-heading">Run Metadata</div>
                    <div class="metadata-grid">
                        ${metadataItem("Mode", titleCase(run.mode || report?.header?.mode || "unknown"))}
                        ${metadataItem("Ticker", run.ticker || report?.config_resolved?.ticker || "N/A")}
                        ${metadataItem("Config Path", report?.header?.config_path || "N/A")}
                        ${metadataItem("Config Hash", report?.header?.config_hash || "N/A")}
                        ${metadataItem("Interval", report?.config_resolved?.interval || "N/A")}
                        ${metadataItem("Fees", report?.config_resolved?.fee ?? "N/A")}
                    </div>
                </article>
                <article class="detail-panel glass">
                    <div class="panel-heading">Artifacts</div>
                    <div class="artifact-list">
                        ${artifacts.length ? artifacts.map((artifact) => `<a class="artifact-row" href="${run.path}/${artifact.file_name}" target="_blank" rel="noreferrer"><span class="artifact-name">${escapeHtml(artifact.file_name)}</span><span class="artifact-size">${formatBytes(artifact.size_bytes)}</span></a>`).join("") : `<div class="empty-inline">No artifact manifest exposed in the loaded report.</div>`}
                    </div>
                </article>
            </section>
            ${report?.reproduce?.command ? `<section class="detail-panel glass"><div class="panel-heading">Reproduce</div><div class="code-block">${escapeHtml(report.reproduce.command)}</div></section>` : ""}
            <section class="detail-panel glass">
                <div class="panel-heading">Result Surface</div>
                ${rows.length ? `
                    <div class="detail-table-wrap">
                        <table class="detail-table">
                            <thead><tr>${columns.map((column) => `<th>${escapeHtml(titleCase(column.replace(/_/g, " ")))}</th>`).join("")}</tr></thead>
                            <tbody>${rows.map((row) => `<tr>${columns.map((column) => `<td>${formatCell(row[column])}</td>`).join("")}</tr>`).join("")}</tbody>
                        </table>
                    </div>
                ` : `<div class="empty-inline">No tabular result rows available for this run.</div>`}
            </section>
        </div>
    `;
}

function setRegistryState(status, detail = "") {
    if (status === "ready") {
        elements.registryStatus.textContent = "Registry: Connected";
        elements.registryDate.textContent = `Artifact: ${formatDateTime(state.generatedAt)}`;
        elements.registryDot.classList.add("pulse");
        elements.heroRegistryPill.textContent = "Registry online";
        return;
    }
    if (status === "syncing") {
        elements.registryStatus.textContent = "Registry: Syncing";
        elements.registryDate.textContent = state.generatedAt ? `Artifact: ${formatDateTime(state.generatedAt)}` : "Artifact: syncing...";
        elements.registryDot.classList.add("pulse");
        elements.heroRegistryPill.textContent = "Registry syncing";
        return;
    }
    elements.registryStatus.textContent = "Registry: Error";
    elements.registryDate.textContent = `Artifact: ${detail || "unavailable"}`;
    elements.registryDot.classList.remove("pulse");
    elements.heroRegistryPill.textContent = "Registry offline";
}

function metricCard(label, value, toneClass) {
    return `<article class="metric-card glass ${toneClass}"><div class="metric-label">${escapeHtml(label)}</div><div class="metric-value">${escapeHtml(value)}</div></article>`;
}

function metadataItem(label, value) {
    return `<div class="meta-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value))}</strong></div>`;
}

function formatCell(value) {
    if (value == null) {
        return '<span class="muted">-</span>';
    }
    if (typeof value === "number") {
        return Number.isInteger(value) ? String(value) : value.toFixed(3);
    }
    if (typeof value === "boolean") {
        return value ? "Yes" : "No";
    }
    return escapeHtml(String(value));
}

function notify(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    elements.toastContainer.appendChild(toast);
    window.setTimeout(() => toast.classList.add("toast-visible"), 10);
    window.setTimeout(() => {
        toast.classList.remove("toast-visible");
        window.setTimeout(() => toast.remove(), 250);
    }, 2800);
}

function normalizePath(path) { return `/${String(path).replace(/\\/g, "/").replace(/^\.?\//, "")}`; }
function preferredReportHref(run) {
    const markdown = run.mode === "grid" || run.mode === "walkforward" || run.mode === "sweep"
        ? "run_report.md"
        : "report.md";
    return `${run.path}/${markdown}`;
}
function toNumber(value) { const number = Number(value); return Number.isFinite(number) ? number : null; }
function average(values) { return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null; }
function isNumber(value) { return typeof value === "number" && Number.isFinite(value); }
function formatPercent(value) { return value == null ? "-" : `${(value * 100).toFixed(2)}%`; }
function formatNumber(value) { return value == null ? "-" : Number(value).toFixed(2); }
function formatCount(value) { return value == null ? "-" : (Number.isInteger(value) ? String(value) : Number(value).toFixed(1)); }
function formatDateTime(value) { return value ? new Date(value).toLocaleString() : "-"; }
function formatBytes(value) { return value == null ? "-" : value < 1024 ? `${value} B` : value < 1048576 ? `${(value / 1024).toFixed(1)} KB` : `${(value / 1048576).toFixed(1)} MB`; }
function shortCommit(value) { return value ? String(value).slice(0, 7) : ""; }
function titleCase(value) { return String(value || "").split(/[_\s-]+/).filter(Boolean).map((part) => part[0].toUpperCase() + part.slice(1)).join(" "); }
function escapeHtml(value) { return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;"); }
function modeBadge(mode) { return mode === "grid" || mode === "sweep" ? "badge-purple" : mode === "walkforward" || mode === "forward" ? "badge-green" : "badge-blue"; }
function tone(value, positiveIsGood) { if (value == null) { return "tone-neutral"; } return positiveIsGood ? (value >= 0 ? "tone-positive" : "tone-negative") : (value <= -0.15 ? "tone-negative" : "tone-positive"); }
