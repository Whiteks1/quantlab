const CONFIG = {
    registryPath: "/outputs/runs/runs_index.json",
    launchControlPath: "/api/launch-control",
    paperHealthPath: "/api/paper-sessions-health",
    paperAlertsPath: "/api/paper-sessions-alerts",
    brokerHealthPath: "/api/broker-submissions-health",
    hyperliquidSurfacePath: "/api/hyperliquid-surface",
    pretradeHandoffPath: "/api/pretrade-handoff-intake",
    stepbitWorkspacePath: "/api/stepbit-workspace",
    metaTradeWorkspacePath: "/api/meta-trade-workspace",
    detailArtifacts: ["report.json", "run_report.json"],
    refreshIntervalMs: 30000,
};

const state = {
    runs: [],
    filteredRuns: [],
    generatedAt: null,
    sortField: "created_at",
    sortDir: "desc",
    filterMode: "all",
    searchQuery: "",
    selectedRunIds: [],
    currentRunId: null,
    detailCache: new Map(),
    isLoading: false,
    paperHealth: null,
    paperAlerts: null,
    brokerHealth: null,
    hyperliquidSurface: null,
    pretradeIntake: null,
    stepbitWorkspace: null,
    metaTradeWorkspace: null,
    launchControl: null,
    lastSyncAt: null,
    nextSyncAt: null,
    isSubmittingLaunch: false,
};

const elements = {
    breadcrumb: document.getElementById("breadcrumb"),
    refreshBtn: document.getElementById("refresh-data"),
    searchInput: document.getElementById("run-search"),
    syncMeta: document.getElementById("sync-meta"),
    surfaceSummary: document.getElementById("surface-summary"),
    registryDot: document.getElementById("registry-dot"),
    registryStatus: document.getElementById("registry-status"),
    registryDate: document.getElementById("registry-date"),
    sidebarBoundaryMeta: document.getElementById("sidebar-boundary-meta"),
    launchSummary: document.getElementById("launch-summary"),
    launchForm: document.getElementById("launch-form"),
    launchCommand: document.getElementById("launch-command"),
    launchInterval: document.getElementById("launch-interval"),
    launchInitialCash: document.getElementById("launch-initial-cash"),
    launchTicker: document.getElementById("launch-ticker"),
    launchStart: document.getElementById("launch-start"),
    launchEnd: document.getElementById("launch-end"),
    launchRunFields: document.getElementById("launch-run-fields"),
    launchSweepFields: document.getElementById("launch-sweep-fields"),
    launchConfigPath: document.getElementById("launch-config-path"),
    launchOutDir: document.getElementById("launch-out-dir"),
    launchPaper: document.getElementById("launch-paper"),
    launchSubmit: document.getElementById("launch-submit"),
    launchStepbitBtn: document.getElementById("launch-stepbit"),
    launchFeedback: document.getElementById("launch-feedback"),
    launchStepbitMeta: document.getElementById("launch-stepbit-meta"),
    launchStepbitRuntime: document.getElementById("launch-stepbit-runtime"),
    openStepbitLink: document.getElementById("open-stepbit"),
    launchJobsMeta: document.getElementById("launch-jobs-meta"),
    launchJobsBody: document.getElementById("launch-jobs-body"),
    runsSummary: document.getElementById("runs-summary"),
    visibleRuns: document.getElementById("summary-visible-runs"),
    freshRuns: document.getElementById("summary-fresh-runs"),
    bestSharpe: document.getElementById("summary-best-sharpe"),
    averageReturn: document.getElementById("summary-average-return"),
    modePills: document.getElementById("mode-pills"),
    modeFilter: document.getElementById("filter-mode"),
    clearFiltersBtn: document.getElementById("clear-filters"),
    compareSummary: document.getElementById("compare-summary"),
    openCompareLink: document.getElementById("open-compare"),
    clearCompareBtn: document.getElementById("clear-compare"),
    runsBody: document.getElementById("runs-body"),
    compareSummaryLong: document.getElementById("compare-summary-long"),
    compareBody: document.getElementById("compare-body"),
    opsSummary: document.getElementById("ops-summary"),
    paperSummary: document.getElementById("paper-summary"),
    paperPanelBody: document.getElementById("paper-panel-body"),
    pretradeSummary: document.getElementById("pretrade-summary"),
    pretradePanelBody: document.getElementById("pretrade-panel-body"),
    paperTotalSessions: document.getElementById("paper-total-sessions"),
    paperHealthMeta: document.getElementById("paper-health-meta"),
    brokerTotalSessions: document.getElementById("broker-total-sessions"),
    brokerHealthMeta: document.getElementById("broker-health-meta"),
    hyperliquidState: document.getElementById("hyperliquid-state"),
    hyperliquidMeta: document.getElementById("hyperliquid-meta"),
    stepbitState: document.getElementById("stepbit-state"),
    stepbitMeta: document.getElementById("stepbit-meta"),
    metaTradeState: document.getElementById("meta-trade-state"),
    metaTradeMeta: document.getElementById("meta-trade-meta"),
    detailBody: document.getElementById("detail-body"),
    views: {
        launch: document.getElementById("launch-view"),
        runs: document.getElementById("runs-view"),
        compare: document.getElementById("compare-view"),
        ops: document.getElementById("ops-view"),
        detail: document.getElementById("detail-view"),
    },
    navItems: {
        launch: document.getElementById("nav-launch"),
        runs: document.getElementById("nav-runs"),
        compare: document.getElementById("nav-compare"),
        ops: document.getElementById("nav-ops"),
    },
};

document.addEventListener("DOMContentLoaded", () => {
    elements.refreshBtn.addEventListener("click", () => fetchAll(true));
    elements.searchInput.addEventListener("input", (event) => {
        state.searchQuery = String(event.target.value || "").trim().toLowerCase();
        applyFilters();
    });
    elements.modeFilter.addEventListener("change", (event) => {
        state.filterMode = event.target.value;
        syncModePills();
        applyFilters();
    });
    elements.launchCommand.addEventListener("change", renderLaunch);
    elements.launchForm.addEventListener("submit", submitLaunch);
    elements.launchStepbitBtn.addEventListener("click", startStepbitWorkspace);
    elements.clearFiltersBtn.addEventListener("click", resetFilters);
    elements.clearCompareBtn.addEventListener("click", clearCompareSelection);
    elements.openCompareLink.addEventListener("click", (event) => {
        if (state.selectedRunIds.length < 2) {
            event.preventDefault();
        }
    });
    elements.runsBody.addEventListener("change", handleCompareSelectionChange);
    document.querySelectorAll("th[data-sort]").forEach((header) => {
        header.addEventListener("click", () => {
            const field = header.dataset.sort;
            if (!field) {
                return;
            }
            state.sortDir = state.sortField === field && state.sortDir === "desc" ? "asc" : "desc";
            state.sortField = field;
            updateSortHeaders();
            applyFilters();
        });
    });
    elements.modePills.addEventListener("click", (event) => {
        const button = event.target.closest("[data-mode]");
        if (!button) {
            return;
        }
        state.filterMode = button.dataset.mode || "all";
        elements.modeFilter.value = state.filterMode;
        syncModePills();
        applyFilters();
    });
    window.addEventListener("hashchange", route);
    window.setInterval(() => fetchAll(false, true), CONFIG.refreshIntervalMs);
    window.setInterval(updateSyncMeta, 1000);
    updateSortHeaders();
    fetchAll();
    route();
});

async function fetchAll(showNotice = false, silent = false) {
    state.isLoading = true;
    renderTable();
    renderLaunch();
    setRegistryStatus("syncing");

    try {
        const registryResponse = await fetchJson(CONFIG.registryPath);
        const [launchControl, paperHealth, paperAlerts, brokerHealth, hyperliquidSurface, pretradeIntake, stepbitWorkspace, metaTradeWorkspace] = await Promise.all([
            fetchJsonSafe(CONFIG.launchControlPath, {
                status: "error",
                available: false,
                supported_commands: ["run", "sweep"],
                jobs: [],
                message: "Launch control unavailable.",
            }),
            fetchJsonSafe(CONFIG.paperHealthPath, {
                status: "error",
                available: false,
                total_sessions: 0,
                status_counts: {},
                message: "Paper health unavailable.",
            }),
            fetchJsonSafe(CONFIG.paperAlertsPath, {
                status: "error",
                available: false,
                total_sessions: 0,
                status_counts: {},
                alert_counts: {},
                alerts: [],
                message: "Paper alerts unavailable.",
            }),
            fetchJsonSafe(CONFIG.brokerHealthPath, {
                status: "error",
                available: false,
                total_sessions: 0,
                status_counts: {},
                alert_counts: {},
                alerts: [],
                message: "Broker health unavailable.",
            }),
            fetchJsonSafe(CONFIG.hyperliquidSurfacePath, {
                status: "error",
                available: false,
                implemented_surfaces: {},
                latest_artifacts: {},
                message: "Hyperliquid surface unavailable.",
            }),
            fetchJsonSafe(CONFIG.pretradeHandoffPath, {
                status: "error",
                available: false,
                has_validation: false,
                validation_state: "error",
                reasons: [],
                message: "Pre-trade intake unavailable.",
            }),
            fetchJsonSafe(CONFIG.stepbitWorkspacePath, {
                status: "error",
                available: false,
                live_urls: {},
                start_support: {},
                start_state: { status: "idle", actions: [] },
                repos: {},
                workspace_summary: {},
                boundary_note: "Stepbit workspace unavailable.",
            }),
            fetchJsonSafe(CONFIG.metaTradeWorkspacePath, {
                status: "error",
                available: false,
                repo: { present: false },
                workspace_summary: {},
                boundary_note: "meta_trade workspace unavailable.",
            }),
        ]);

        state.runs = (registryResponse.runs || []).map(normalizeRun);
        state.generatedAt = registryResponse.generated_at || null;
        state.launchControl = launchControl;
        state.paperHealth = paperHealth;
        state.paperAlerts = paperAlerts;
        state.brokerHealth = brokerHealth;
        state.hyperliquidSurface = hyperliquidSurface;
        state.pretradeIntake = pretradeIntake;
        state.stepbitWorkspace = stepbitWorkspace;
        state.metaTradeWorkspace = metaTradeWorkspace;
        state.detailCache.clear();
        state.selectedRunIds = state.selectedRunIds.filter((runId) => state.runs.some((run) => run.run_id === runId));
        state.lastSyncAt = Date.now();
        state.nextSyncAt = Date.now() + CONFIG.refreshIntervalMs;

        populateModeFilter();
        applyFilters();
        renderLaunch();
        renderOps();
        setRegistryStatus("ready");

        if (showNotice && !silent) {
            elements.surfaceSummary.textContent = "Registry and operational surfaces refreshed.";
        }

        if (state.currentRunId) {
            await loadRunDetail(state.currentRunId, true);
        }
    } catch (error) {
        state.runs = [];
        state.filteredRuns = [];
        state.launchControl = null;
        setRegistryStatus("error", error.message);
        elements.surfaceSummary.textContent = `Backend load failed: ${error.message}`;
        renderLaunch();
        renderTable();
    } finally {
        state.isLoading = false;
        updateSyncMeta();
    }
}

async function fetchJson(path) {
    const response = await fetch(`${path}?t=${Date.now()}`);
    if (!response.ok) {
        throw new Error(`${path} returned ${response.status}`);
    }
    return response.json();
}

async function fetchJsonSafe(path, fallback) {
    try {
        return await fetchJson(path);
    } catch (error) {
        return {
            ...fallback,
            message: error.message || fallback.message || `${path} unavailable`,
        };
    }
}

function normalizeRun(run) {
    return {
        ...run,
        total_return: toNumber(run.total_return),
        sharpe_simple: toNumber(run.sharpe_simple),
        max_drawdown: toNumber(run.max_drawdown),
        trades: toNumber(run.trades),
        path: normalizePath(run.path),
    };
}

function applyFilters() {
    let runs = [...state.runs];

    if (state.searchQuery) {
        runs = runs.filter((run) => {
            const values = [run.run_id, run.mode, run.ticker, run.git_commit, run.start, run.end].filter(Boolean);
            return values.some((value) => String(value).toLowerCase().includes(state.searchQuery));
        });
    }

    if (state.filterMode !== "all") {
        runs = runs.filter((run) => run.mode === state.filterMode);
    }

    runs.sort(compareRuns);
    state.filteredRuns = runs;
    renderRunsSummary();
    renderTable();
    renderCompare();
}

function compareRuns(left, right) {
    const a = left[state.sortField];
    const b = right[state.sortField];
    const direction = state.sortDir === "asc" ? 1 : -1;

    if (a == null && b == null) {
        return 0;
    }
    if (a == null) {
        return 1;
    }
    if (b == null) {
        return -1;
    }
    if (state.sortField === "created_at") {
        return (new Date(a).getTime() - new Date(b).getTime()) * direction;
    }
    if (typeof a === "number" && typeof b === "number") {
        return (a - b) * direction;
    }
    return String(a).localeCompare(String(b)) * direction;
}

function populateModeFilter() {
    const modes = ["all", ...new Set(state.runs.map((run) => run.mode).filter(Boolean))];
    elements.modeFilter.innerHTML = modes
        .map((mode) => `<option value="${escapeHtml(mode)}">${escapeHtml(mode === "all" ? "All modes" : titleCase(mode))}</option>`)
        .join("");
    elements.modeFilter.value = state.filterMode;
    elements.modePills.innerHTML = modes
        .map((mode) => `<button class="mode-pill${mode === state.filterMode ? " active" : ""}" type="button" data-mode="${escapeHtml(mode)}">${escapeHtml(mode === "all" ? "All" : titleCase(mode))}</button>`)
        .join("");
}

function syncModePills() {
    elements.modePills.querySelectorAll("[data-mode]").forEach((button) => {
        button.classList.toggle("active", button.dataset.mode === state.filterMode);
    });
}

function resetFilters() {
    state.searchQuery = "";
    state.filterMode = "all";
    elements.searchInput.value = "";
    elements.modeFilter.value = "all";
    syncModePills();
    applyFilters();
}

function clearCompareSelection() {
    state.selectedRunIds = [];
    renderTable();
    renderCompare();
}

function handleCompareSelectionChange(event) {
    const input = event.target.closest("[data-compare-run]");
    if (!input) {
        return;
    }
    const runId = input.dataset.compareRun;
    if (!runId) {
        return;
    }

    if (input.checked) {
        if (!state.selectedRunIds.includes(runId)) {
            state.selectedRunIds = [...state.selectedRunIds, runId].slice(0, 4);
        }
    } else {
        state.selectedRunIds = state.selectedRunIds.filter((id) => id !== runId);
    }

    renderTable();
    renderCompare();
}

function renderRunsSummary() {
    const freshCount = state.runs.filter((run) => run.created_at && (Date.now() - new Date(run.created_at).getTime()) <= 86400000).length;
    const bestRun = [...state.runs]
        .filter((run) => isFiniteNumber(run.sharpe_simple))
        .sort((a, b) => b.sharpe_simple - a.sharpe_simple)[0];
    const avgReturn = average(state.runs.map((run) => run.total_return).filter(isFiniteNumber));

    elements.visibleRuns.textContent = String(state.filteredRuns.length);
    elements.freshRuns.textContent = String(freshCount);
    elements.bestSharpe.textContent = bestRun ? formatNumber(bestRun.sharpe_simple) : "-";
    elements.averageReturn.textContent = formatPercent(avgReturn);
    elements.runsSummary.textContent = state.runs.length
        ? `${state.filteredRuns.length} visible of ${state.runs.length} indexed runs. Explore, open detail, or compare actual results.`
        : "No runs indexed yet. When backend artifacts exist, they will appear here.";

    updateCompareSummary();
    updateSurfaceSummary();
}

function updateCompareSummary() {
    const count = state.selectedRunIds.length;
    elements.compareSummary.textContent = count ? `${count} selected` : "Select 2 to 4 runs";
    elements.compareSummaryLong.textContent = count >= 2
        ? `Comparing ${count} real runs from the registry.`
        : "Select runs from the explorer to compare actual results side by side.";
    elements.clearCompareBtn.disabled = count === 0;
    elements.openCompareLink.classList.toggle("is-disabled", count < 2);
    elements.openCompareLink.setAttribute("aria-disabled", count < 2 ? "true" : "false");
}

function renderTable() {
    if (state.isLoading && !state.runs.length) {
        elements.runsBody.innerHTML = `<tr><td colspan="9" class="table-empty">Loading runs...</td></tr>`;
        return;
    }

    if (!state.runs.length) {
        elements.runsBody.innerHTML = `<tr><td colspan="9" class="table-empty">No run index found at <code>outputs/runs/runs_index.json</code>.</td></tr>`;
        return;
    }

    if (!state.filteredRuns.length) {
        elements.runsBody.innerHTML = `<tr><td colspan="9" class="table-empty">No runs match the current filters.</td></tr>`;
        return;
    }

    elements.runsBody.innerHTML = state.filteredRuns.map((run) => {
        const selected = state.selectedRunIds.includes(run.run_id);
        const disableSelection = !selected && state.selectedRunIds.length >= 4;
        return `
            <tr>
                <td>
                    <label class="compare-check">
                        <input type="checkbox" data-compare-run="${escapeHtml(run.run_id || "")}" ${selected ? "checked" : ""} ${disableSelection ? "disabled" : ""}>
                        <span></span>
                    </label>
                </td>
                <td>
                    <div class="run-cell">
                        <strong>${escapeHtml(run.run_id || "unknown")}</strong>
                        <span>${escapeHtml(shortCommit(run.git_commit) || "no commit")}</span>
                    </div>
                </td>
                <td><span class="mode-badge">${escapeHtml(titleCase(run.mode || "unknown"))}</span></td>
                <td>${escapeHtml(run.ticker || "-")}</td>
                <td class="${toneClass(run.total_return, true)}">${formatPercent(run.total_return)}</td>
                <td>${formatNumber(run.sharpe_simple)}</td>
                <td class="${toneClass(run.max_drawdown, false)}">${formatPercent(run.max_drawdown)}</td>
                <td>${formatDateTime(run.created_at)}</td>
                <td><a class="text-link" href="#/run/${encodeURIComponent(run.run_id)}">Open</a></td>
            </tr>
        `;
    }).join("");
}

function renderCompare() {
    updateCompareSummary();

    const selectedRuns = state.selectedRunIds
        .map((runId) => state.runs.find((run) => run.run_id === runId))
        .filter(Boolean);

    if (selectedRuns.length < 2) {
        elements.compareBody.innerHTML = `
            <div class="panel-empty">
                <strong>No comparison selected</strong>
                <span>Choose 2 to 4 runs in the explorer and open compare.</span>
            </div>
        `;
        return;
    }

    elements.compareBody.innerHTML = selectedRuns.map((run) => `
        <article class="compare-card">
            <div class="compare-card-header">
                <div>
                    <div class="section-label">${escapeHtml(titleCase(run.mode || "unknown"))}</div>
                    <h3>${escapeHtml(run.run_id)}</h3>
                </div>
                <a class="text-link" href="#/run/${encodeURIComponent(run.run_id)}">Detail</a>
            </div>
            <div class="compare-meta">${escapeHtml(run.ticker || "-")} · ${formatDateTime(run.created_at)}</div>
            <dl class="compare-metrics">
                ${compareMetric("Return", formatPercent(run.total_return), toneClass(run.total_return, true))}
                ${compareMetric("Sharpe", formatNumber(run.sharpe_simple), "")}
                ${compareMetric("Drawdown", formatPercent(run.max_drawdown), toneClass(run.max_drawdown, false))}
                ${compareMetric("Trades", formatCount(run.trades), "")}
                ${compareMetric("Window", `${run.start || "-"} → ${run.end || "-"}`, "")}
            </dl>
        </article>
    `).join("");
}

function renderLaunch() {
    const command = elements.launchCommand.value || "run";
    const isRun = command === "run";
    elements.launchRunFields.classList.toggle("hidden", !isRun);
    elements.launchSweepFields.classList.toggle("hidden", isRun);
    elements.launchPaper.closest(".check-field").classList.toggle("hidden", !isRun);
    elements.launchInterval.closest(".field").classList.toggle("hidden", !isRun);
    elements.launchInitialCash.closest(".field").classList.toggle("hidden", !isRun);

    const launchControl = state.launchControl;
    const jobs = Array.isArray(launchControl?.jobs) ? launchControl.jobs : [];
    const stepbit = state.stepbitWorkspace || {};
    const liveUrls = stepbit.live_urls || {};
    const startSupport = stepbit.start_support || {};
    const startState = stepbit.start_state || {};
    const stepbitReachable = Boolean(liveUrls.reachable);
    const frontendUp = Boolean(liveUrls.frontend_reachable);
    const backendUp = Boolean(liveUrls.backend_reachable);
    const coreUp = Boolean(liveUrls.core_reachable);
    const coreReady = Boolean(liveUrls.core_ready);
    const preferredStepbitUrl = liveUrls.preferred_url || stepbit.live_preview_url || "#";
    const canLaunchStepbit = Boolean(stepbit.available && (startSupport.can_start_backend || startSupport.can_start_frontend));
    const stepbitStarting = startState.status === "starting";
    const runtimeSummary = [
        `Frontend ${frontendUp ? "up" : "down"}`,
        `Backend ${backendUp ? "up" : "down"}`,
        `Core ${coreUp ? (coreReady ? "ready" : "up") : "unavailable"}`,
    ].join(" · ");

    elements.launchSummary.textContent = launchControl
        ? `Launch ${launchControl.supported_commands.join(" or ")} from QuantLab, then use Stepbit as planner or analysis support.`
        : "Loading launcher state...";
    elements.launchJobsMeta.textContent = jobs.length ? `${jobs.length} recent jobs` : "No launches recorded yet";
    elements.launchStepbitMeta.textContent = stepbitReachable
        ? `Stepbit workspace reachable at ${preferredStepbitUrl}`
        : (stepbitStarting
            ? "Stepbit AI is starting. Give it a few seconds before retrying."
            : canLaunchStepbit
            ? "Stepbit is optional. QuantLab can start the local app surface for you."
            : "Stepbit is optional. This machine is missing the commands needed to auto-start it.");
    elements.launchStepbitRuntime.innerHTML = [
        renderRuntimeChip("Frontend", frontendUp ? "up" : "down", frontendUp ? "up" : "down"),
        renderRuntimeChip("Backend", backendUp ? "up" : "down", backendUp ? "up" : "down"),
        renderRuntimeChip("Core", coreUp ? (coreReady ? "ready" : "up") : "unavailable", coreUp ? (coreReady ? "up" : "warn") : "down"),
    ].join("");
    elements.openStepbitLink.href = preferredStepbitUrl;
    elements.openStepbitLink.classList.toggle("is-disabled", !stepbitReachable);
    elements.openStepbitLink.setAttribute("aria-disabled", stepbitReachable ? "false" : "true");
    elements.launchStepbitBtn.disabled = !canLaunchStepbit || stepbitReachable || stepbitStarting;
    elements.launchStepbitBtn.textContent = stepbitStarting ? `Starting Stepbit AI · ${runtimeSummary}` : `Launch Stepbit AI · ${runtimeSummary}`;
    elements.openStepbitLink.textContent = `Open Stepbit AI · ${runtimeSummary}`;
    elements.launchSubmit.disabled = state.isSubmittingLaunch;
    elements.launchSubmit.textContent = state.isSubmittingLaunch ? "Launching..." : "Launch in QuantLab";

    if (!jobs.length) {
        elements.launchJobsBody.innerHTML = `
            <div class="panel-empty">
                <strong>No launches yet</strong>
                <span>Use the form to start a run or sweep.</span>
            </div>
        `;
        return;
    }

    elements.launchJobsBody.innerHTML = jobs.map((job) => `
        <article class="launch-job">
            <div class="launch-job-top">
                <div>
                    <strong>${escapeHtml(titleCase(job.command || "unknown"))}</strong>
                    <span class="launch-job-id">${escapeHtml(job.request_id || "-")}</span>
                </div>
                <span class="mode-badge ${launchStatusClass(job.status)}">${escapeHtml(titleCase(job.status || "unknown"))}</span>
            </div>
            <div class="launch-job-summary">${escapeHtml(job.summary || "-")}</div>
            <div class="launch-job-meta">${escapeHtml(formatDateTime(job.started_at))}${job.ended_at ? ` · ended ${escapeHtml(formatDateTime(job.ended_at))}` : " · in progress"}</div>
            ${job.error_message ? `<div class="launch-job-error">${escapeHtml(job.error_message)}</div>` : ""}
            <div class="launch-job-links">
                ${job.artifacts_href ? `<a class="text-link" href="${job.artifacts_href}" target="_blank" rel="noreferrer">Artifacts</a>` : ""}
                ${job.report_href ? `<a class="text-link" href="${job.report_href}" target="_blank" rel="noreferrer">Report</a>` : ""}
                ${job.stdout_href ? `<a class="text-link" href="${job.stdout_href}" target="_blank" rel="noreferrer">Stdout</a>` : ""}
                ${job.stderr_href ? `<a class="text-link" href="${job.stderr_href}" target="_blank" rel="noreferrer">Stderr</a>` : ""}
            </div>
        </article>
    `).join("");
}

async function submitLaunch(event) {
    event.preventDefault();

    const command = elements.launchCommand.value || "run";
    const payload = {
        command,
        params: command === "run"
            ? {
                ticker: elements.launchTicker.value.trim(),
                start: elements.launchStart.value,
                end: elements.launchEnd.value,
                interval: elements.launchInterval.value.trim(),
                paper: elements.launchPaper.checked,
                initial_cash: elements.launchInitialCash.value.trim(),
            }
            : {
                config_path: elements.launchConfigPath.value.trim(),
                out_dir: elements.launchOutDir.value.trim(),
            },
    };

    state.isSubmittingLaunch = true;
    elements.launchFeedback.textContent = "Submitting launch request...";
    renderLaunch();

    try {
        const response = await fetch(CONFIG.launchControlPath, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.message || `Launch failed with ${response.status}`);
        }

        elements.launchFeedback.textContent = result.message || "Launch accepted.";
        await fetchAll(false, true);
        window.location.hash = "#/launch";
    } catch (error) {
        elements.launchFeedback.textContent = error.message || "Launch failed.";
    } finally {
        state.isSubmittingLaunch = false;
        renderLaunch();
    }
}

async function startStepbitWorkspace() {
    elements.launchFeedback.textContent = "Starting Stepbit AI...";
    elements.launchStepbitBtn.disabled = true;

    try {
        const response = await fetch("/api/stepbit-workspace/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ source: "quantlab_research_ui" }),
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.message || `Stepbit start failed with ${response.status}`);
        }

        elements.launchFeedback.textContent = result.message || "Stepbit launch requested.";
        renderLaunch();
        window.setTimeout(() => fetchAll(false, true), 1200);
        window.setTimeout(() => fetchAll(false, true), 4000);
        window.setTimeout(() => fetchAll(false, true), 8000);
    } catch (error) {
        elements.launchFeedback.textContent = error.message || "Stepbit launch failed.";
        renderLaunch();
    }
}

function compareMetric(label, value, extraClass) {
    return `
        <div class="compare-metric ${extraClass}">
            <dt>${escapeHtml(label)}</dt>
            <dd>${escapeHtml(value)}</dd>
        </div>
    `;
}

function renderRuntimeChip(label, value, tone) {
    return `
        <span class="runtime-chip runtime-${escapeHtml(tone)}">
            <strong>${escapeHtml(label)}</strong>
            <span>${escapeHtml(value)}</span>
        </span>
    `;
}

function renderOps() {
    const paperHealth = state.paperHealth || {};
    const paperAlerts = state.paperAlerts || {};
    const brokerHealth = state.brokerHealth || {};
    const hyperliquidSurface = state.hyperliquidSurface || {};
    const pretradeIntake = state.pretradeIntake || {};
    const stepbitWorkspace = state.stepbitWorkspace || {};
    const metaTradeWorkspace = state.metaTradeWorkspace || {};

    elements.paperTotalSessions.textContent = String(paperHealth.total_sessions || 0);
    elements.paperHealthMeta.textContent = buildPaperMeta(paperHealth, paperAlerts);
    elements.paperSummary.textContent = buildPaperSummary(paperHealth, paperAlerts);
    elements.paperPanelBody.innerHTML = buildPaperPanel(paperHealth, paperAlerts);
    elements.brokerTotalSessions.textContent = String(brokerHealth.total_sessions || 0);
    elements.brokerHealthMeta.textContent = buildBrokerMeta(brokerHealth);
    elements.hyperliquidState.textContent = buildHyperliquidState(hyperliquidSurface);
    elements.hyperliquidMeta.textContent = buildHyperliquidMeta(hyperliquidSurface);
    elements.pretradeSummary.textContent = buildPretradeSummary(pretradeIntake);
    elements.pretradePanelBody.innerHTML = buildPretradePanel(pretradeIntake);
    elements.stepbitState.textContent = stepbitWorkspace.live_urls?.reachable ? "Live" : (stepbitWorkspace.available ? "Attached" : "Boundary");
    elements.stepbitMeta.textContent = buildStepbitMeta(stepbitWorkspace);
    elements.metaTradeState.textContent = metaTradeWorkspace.available ? "Ready" : "Boundary";
    elements.metaTradeMeta.textContent = buildMetaTradeMeta(metaTradeWorkspace);
    elements.opsSummary.textContent = buildOpsSummary(paperHealth, paperAlerts, brokerHealth, hyperliquidSurface, pretradeIntake);
    elements.sidebarBoundaryMeta.textContent = [
        stepbitWorkspace.available ? "Stepbit connected" : "Stepbit boundary",
        metaTradeWorkspace.available ? "Meta Trade connected" : "Meta Trade boundary",
    ].join(" · ");
}

function buildPretradeSummary(pretrade) {
    if (pretrade.status === "error") {
        return "Pre-trade validation is unavailable.";
    }
    if (!pretrade.available) {
        return "No pre-trade root found yet.";
    }
    if (!pretrade.has_validation) {
        return "Waiting for the first validation artifact.";
    }
    return pretrade.accepted
        ? `Latest handoff ${pretrade.handoff_id || "-"} accepted`
        : `Latest handoff ${pretrade.handoff_id || "-"} rejected`;
}

function buildPretradePanel(pretrade) {
    if (pretrade.status === "error") {
        return `
            <div class="panel-empty">
                <strong>Pre-trade validation unavailable</strong>
                <span>${escapeHtml(pretrade.message || "The endpoint could not load the latest artifact.")}</span>
            </div>
        `;
    }

    if (!pretrade.available || !pretrade.has_validation) {
        return `
            <div class="panel-empty">
                <strong>No validation artifact yet</strong>
                <span>${escapeHtml(pretrade.message || "QuantLab will show the latest bounded handoff here when one exists.")}</span>
            </div>
        `;
    }

    const reasons = Array.isArray(pretrade.reasons) && pretrade.reasons.length
        ? pretrade.reasons.map((reason) => `<span class="inline-chip">${escapeHtml(reason)}</span>`).join("")
        : `<span class="muted-copy">No rejection reasons.</span>`;
    const artifactEntries = [
        {
            label: "Validation artifact",
            path: pretrade.latest_validation_path,
            href: pretrade.latest_validation_href,
            fallback: "Latest validation artifact not available yet.",
        },
        {
            label: "Source artifact",
            path: pretrade.source_artifact_path,
            href: pretrade.source_artifact_href,
            fallback: "Source artifact not available yet.",
        },
    ].filter((artifact) => artifact.path || artifact.href);

    const artifactLinks = artifactEntries.length
        ? `
            <div class="artifact-list">
                ${artifactEntries.map((artifact) => {
                    const label = escapeHtml(artifact.label);
                    const path = escapeHtml(artifact.path || artifact.fallback);
                    if (artifact.href) {
                        return `
                            <a class="artifact-link" href="${escapeHtml(artifact.href)}" target="_blank" rel="noreferrer">
                                <span>${label}</span>
                                <span>${path}</span>
                            </a>
                        `;
                    }
                    return `
                        <div class="artifact-link">
                            <span>${label}</span>
                            <span>${path}</span>
                        </div>
                    `;
                }).join("")}
            </div>
        `
        : `
            <div class="panel-empty compact-empty">
                <strong>No artifact paths yet</strong>
                <span>QuantLab will show the validation and source artifact paths here once the first bounded handoff is ingested.</span>
            </div>
        `;

    return `
        <div class="key-value-grid">
            ${keyValue("Handoff", pretrade.handoff_id || "-")}
            ${keyValue("State", pretrade.accepted ? "Accepted" : "Rejected")}
            ${keyValue("Symbol", pretrade.symbol || "-")}
            ${keyValue("Venue", titleCase(pretrade.venue || "-"))}
            ${keyValue("Side", titleCase(pretrade.side || "-"))}
            ${keyValue("Draft ready", pretrade.ready_for_draft_execution_intent ? "Yes" : "No")}
        </div>
        ${artifactLinks}
        <div class="inline-list">${reasons}</div>
    `;
}

function keyValue(label, value) {
    return `
        <div class="key-value-item">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
        </div>
    `;
}

function buildPaperMeta(health, alerts) {
    if (health.status === "error") {
        return health.message || "Paper health unavailable";
    }
    if (!health.available) {
        return "No paper session root yet.";
    }
    if (alerts?.available && alerts.has_alerts) {
        const latestAlert = alerts.latest_alert_code ? titleCase(alerts.latest_alert_code) : "Alert active";
        return `${latestAlert} · threshold ${alerts.stale_after_minutes || "-"}m`;
    }
    return health.latest_session_id
        ? `${health.latest_session_id} · ${titleCase(health.latest_session_status || "unknown")}`
        : "No paper sessions yet.";
}

function buildPaperSummary(health, alerts) {
    if (health.status === "error" || alerts.status === "error") {
        return "Paper operations unavailable.";
    }
    if (!health.available) {
        return "Waiting for the first paper session root.";
    }
    if (alerts.has_alerts) {
        return `${alerts.alerts?.length || 0} active alert(s) across ${health.total_sessions || 0} session(s)`;
    }
    if ((alerts.running_sessions || []).length) {
        return `${alerts.running_sessions.length} running session(s) below stale threshold`;
    }
    return health.latest_session_id
        ? `Latest session ${health.latest_session_id} looks healthy`
        : "No paper sessions recorded yet.";
}

function buildPaperPanel(health, alerts) {
    if (health.status === "error" || alerts.status === "error") {
        const message = alerts.message || health.message || "The paper operations surface could not be loaded.";
        return `
            <div class="panel-empty">
                <strong>Paper operations unavailable</strong>
                <span>${escapeHtml(message)}</span>
            </div>
        `;
    }

    if (!health.available) {
        return `
            <div class="panel-empty">
                <strong>No paper session root yet</strong>
                <span>${escapeHtml(health.message || "QuantLab will surface paper-session operations here once canonical sessions exist.")}</span>
            </div>
        `;
    }

    const statusCounts = health.status_counts || {};
    const alertEntries = Array.isArray(alerts.alerts) ? alerts.alerts.slice(0, 3) : [];
    const signalRow = [
        `<span class="inline-chip ${paperToneClass(alerts.alert_status)}">${escapeHtml(titleCase(alerts.alert_status || "ok"))}</span>`,
        `<span class="inline-chip chip-running">${escapeHtml(`${alerts.running_sessions?.length || 0} running`)}</span>`,
        `<span class="inline-chip chip-calm">${escapeHtml(`stale ${alerts.stale_after_minutes || "-"}m`)}</span>`,
    ].join("");

    const latestSession = health.latest_session_id
        ? `${health.latest_session_id} · ${titleCase(health.latest_session_status || "unknown")}`
        : "No recent session";
    const latestIssue = health.latest_issue_session_id
        ? `${health.latest_issue_session_id} · ${titleCase(health.latest_issue_status || "unknown")}`
        : "No active issues";
    const latestSuccess = alerts.latest_success_session_id
        ? `${alerts.latest_success_session_id} · ${relativeTimeText(alerts.latest_success_at)}`
        : "No successful session yet";

    const alertList = alertEntries.length
        ? `
            <div class="ops-signal-list">
                ${alertEntries.map((alert) => `
                    <article class="signal-row ${alert.severity === "critical" ? "signal-row-attention" : ""}">
                        <strong>${escapeHtml(titleCase(alert.code || "alert"))}</strong>
                        <span>${escapeHtml(alert.message || "Paper session needs attention.")}</span>
                        <div class="signal-meta">${escapeHtml(alert.session_id || "-")} · ${escapeHtml(relativeTimeText(alert.activity_at))}</div>
                    </article>
                `).join("")}
            </div>
        `
        : `
            <div class="panel-empty compact-empty">
                <strong>No active paper alerts</strong>
                <span>Latest paper sessions are either successful or still within the bounded running window.</span>
            </div>
        `;

    return `
        <div class="ops-signal-strip">${signalRow}</div>
        <div class="ops-stat-grid">
            ${opsStat("Latest session", latestSession, relativeTimeText(health.latest_session_at))}
            ${opsStat("Latest issue", latestIssue, health.latest_issue_error_type || relativeTimeText(health.latest_issue_at))}
            ${opsStat("Latest success", latestSuccess, `${statusCounts.success || 0} success`)}
            ${opsStat("Session mix", `${health.total_sessions || 0} total`, `${statusCounts.failed || 0} failed · ${statusCounts.running || 0} running`)}
        </div>
        ${alertList}
    `;
}

function opsStat(label, value, meta) {
    return `
        <article class="ops-stat-card">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value || "-")}</strong>
            <div class="signal-meta">${escapeHtml(meta || "-")}</div>
        </article>
    `;
}

function paperToneClass(status) {
    if (status === "critical") {
        return "chip-attention";
    }
    if (status === "warning") {
        return "chip-running";
    }
    return "chip-calm";
}

function relativeTimeText(value) {
    if (!value) {
        return "No recent activity";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return String(value);
    }
    const diffMs = Date.now() - date.getTime();
    const diffMinutes = Math.max(0, Math.round(diffMs / 60000));
    if (diffMinutes < 1) {
        return "Moments ago";
    }
    if (diffMinutes < 60) {
        return `${diffMinutes}m ago`;
    }
    const diffHours = Math.round(diffMinutes / 60);
    if (diffHours < 24) {
        return `${diffHours}h ago`;
    }
    const diffDays = Math.round(diffHours / 24);
    return `${diffDays}d ago`;
}

function buildBrokerMeta(health) {
    if (health.status === "error") {
        return health.message || "Broker health unavailable";
    }
    if (!health.available) {
        return "No broker validation root yet.";
    }
    return health.latest_submit_session_id
        ? `${health.latest_submit_session_id} · ${titleCase(health.latest_submit_state || "unknown")}`
        : "No broker submissions yet.";
}

function buildHyperliquidState(surface) {
    if (surface.status === "error") {
        return "Error";
    }
    if (!surface.available) {
        return "Unavailable";
    }
    if (surface.submit_has_alerts) {
        return "Attention";
    }
    return "Ready";
}

function buildHyperliquidMeta(surface) {
    if (surface.status === "error") {
        return surface.message || "Hyperliquid surface unavailable";
    }
    if (!surface.available) {
        return "No Hyperliquid artifacts yet.";
    }
    const submitHealth = surface.submit_health || {};
    return submitHealth.latest_submit_session_id
        ? `${submitHealth.latest_submit_session_id} · ${titleCase(submitHealth.latest_submit_state || "unknown")}`
        : "Lifecycle surfaces detected.";
}

function buildStepbitMeta(workspace) {
    if (!workspace.available) {
        return workspace.boundary_note || "External workspace only.";
    }
    const summary = workspace.workspace_summary || {};
    const live = workspace.live_urls?.reachable ? " · live workspace reachable" : "";
    return `${summary.app_surfaces_present || 0} app surfaces · ${summary.core_capabilities_present || 0} core capabilities${live}`;
}

function buildMetaTradeMeta(workspace) {
    if (!workspace.available) {
        return workspace.boundary_note || "External pre-trade workbench only.";
    }
    const summary = workspace.workspace_summary || {};
    return `${summary.product_surfaces_present || 0} workbench surfaces · ${summary.engine_modules_present || 0} engine modules`;
}

function buildOpsSummary(paperHealth, paperAlerts, brokerHealth, hyperliquidSurface, pretradeIntake) {
    const parts = [
        paperAlerts?.has_alerts
            ? `Paper attention ${paperAlerts.alerts?.length || 0}`
            : `Paper ${paperHealth.total_sessions || 0}`,
        `Broker ${brokerHealth.total_sessions || 0}`,
        `Hyperliquid ${buildHyperliquidState(hyperliquidSurface)}`,
    ];
    parts.push(pretradeIntake.has_validation ? (pretradeIntake.accepted ? "Pre-trade accepted" : "Pre-trade rejected") : "Pre-trade pending");
    return parts.join(" · ");
}

function route() {
    const hash = window.location.hash || "#/";

    Object.values(elements.views).forEach((view) => view.classList.remove("active"));
    Object.values(elements.navItems).forEach((item) => item.classList.remove("active"));

    if (hash.startsWith("#/run/")) {
        const runId = decodeURIComponent(hash.split("/")[2] || "");
        state.currentRunId = runId;
        elements.views.detail.classList.add("active");
        elements.navItems.runs.classList.add("active");
        elements.breadcrumb.textContent = "Run detail";
        loadRunDetail(runId);
        return;
    }

    if (hash === "#/compare") {
        state.currentRunId = null;
        elements.views.compare.classList.add("active");
        elements.navItems.compare.classList.add("active");
        elements.breadcrumb.textContent = "Compare";
        renderCompare();
        return;
    }

    if (hash === "#/launch") {
        state.currentRunId = null;
        elements.views.launch.classList.add("active");
        elements.navItems.launch.classList.add("active");
        elements.breadcrumb.textContent = "Launch";
        renderLaunch();
        return;
    }

    if (hash === "#/ops") {
        state.currentRunId = null;
        elements.views.ops.classList.add("active");
        elements.navItems.ops.classList.add("active");
        elements.breadcrumb.textContent = "Ops";
        renderOps();
        return;
    }

    state.currentRunId = null;
    elements.views.runs.classList.add("active");
    elements.navItems.runs.classList.add("active");
    elements.breadcrumb.textContent = "Runs";
}

async function loadRunDetail(runId, silent = false) {
    const run = state.runs.find((entry) => entry.run_id === runId);
    if (!run) {
        elements.detailBody.innerHTML = `
            <div class="panel-empty">
                <strong>Run not found</strong>
                <span>${escapeHtml(runId)} is not present in the current registry snapshot.</span>
                <a class="text-link" href="#/">Back to runs</a>
            </div>
        `;
        return;
    }

    if (state.detailCache.has(runId)) {
        renderDetail(run, state.detailCache.get(runId));
        return;
    }

    if (!silent) {
        elements.detailBody.innerHTML = `
            <div class="panel-empty">
                <strong>Loading run detail</strong>
                <span>Reading canonical artifacts for ${escapeHtml(runId)}...</span>
            </div>
        `;
    }

    let detail = { report: null, reportUrl: null };
    for (const artifact of CONFIG.detailArtifacts) {
        const href = `${toArtifactHref(run.path)}/${artifact}`;
        try {
            const response = await fetch(href);
            if (!response.ok) {
                continue;
            }
            detail = { report: await response.json(), reportUrl: href };
            break;
        } catch (_error) {
            // Keep trying remaining artifacts.
        }
    }

    state.detailCache.set(runId, detail);
    renderDetail(run, detail);
}

function renderDetail(run, detail) {
    const report = detail.report;
    const primary = report?.results?.[0] || report?.oos_leaderboard?.[0] || report?.summary?.[0] || report?.summary || {};
    const artifacts = Array.isArray(report?.artifacts) ? report.artifacts : [];

    elements.detailBody.innerHTML = `
        <div class="detail-shell">
            <div class="detail-top">
                <a class="text-link" href="#/">Back to runs</a>
                ${detail.reportUrl ? `<a class="text-link" href="${detail.reportUrl}" target="_blank" rel="noreferrer">Raw report</a>` : ""}
            </div>

            <div class="detail-header">
                <div>
                    <div class="section-label">${escapeHtml(titleCase(run.mode || "unknown"))}</div>
                    <h2>${escapeHtml(run.run_id)}</h2>
                    <p class="muted-copy">${escapeHtml(run.ticker || "-")} · ${formatDateTime(run.created_at)} · ${escapeHtml(shortCommit(run.git_commit) || "no commit")}</p>
                </div>
            </div>

            <div class="summary-grid">
                <article class="summary-card">
                    <div class="summary-label">Return</div>
                    <div class="summary-value ${toneClass(primary.total_return ?? run.total_return, true)}">${formatPercent(primary.total_return ?? run.total_return)}</div>
                </article>
                <article class="summary-card">
                    <div class="summary-label">Sharpe</div>
                    <div class="summary-value">${formatNumber(primary.sharpe_simple ?? run.sharpe_simple)}</div>
                </article>
                <article class="summary-card">
                    <div class="summary-label">Drawdown</div>
                    <div class="summary-value ${toneClass(primary.max_drawdown ?? run.max_drawdown, false)}">${formatPercent(primary.max_drawdown ?? run.max_drawdown)}</div>
                </article>
                <article class="summary-card">
                    <div class="summary-label">Trades</div>
                    <div class="summary-value">${formatCount(primary.trades ?? run.trades)}</div>
                </article>
            </div>

            <div class="detail-grid">
                <section class="detail-panel">
                    <div class="section-label">Run metadata</div>
                    <div class="key-value-grid">
                        ${keyValue("Window", `${run.start || "-"} → ${run.end || "-"}`)}
                        ${keyValue("Ticker", run.ticker || "-")}
                        ${keyValue("Commit", shortCommit(run.git_commit) || "-")}
                        ${keyValue("Contract", report?.machine_contract?.contract_type || "-")}
                    </div>
                </section>

                <section class="detail-panel">
                    <div class="section-label">Artifacts</div>
                    ${artifacts.length ? `
                        <div class="artifact-list">
                            ${artifacts.map((artifact) => `
                                <a class="artifact-link" href="${toArtifactHref(run.path)}/${artifact.file_name}" target="_blank" rel="noreferrer">
                                    <span>${escapeHtml(artifact.file_name)}</span>
                                    <span>${formatBytes(artifact.size_bytes)}</span>
                                </a>
                            `).join("")}
                        </div>
                    ` : `<div class="panel-empty compact-empty"><strong>No artifact manifest</strong><span>The loaded report does not expose an artifact list.</span></div>`}
                </section>
            </div>
        </div>
    `;
}

function setRegistryStatus(status, detail = "") {
    elements.registryDot.className = "status-dot";

    if (status === "ready") {
        elements.registryDot.classList.add("is-ready");
        elements.registryStatus.textContent = "Registry ready";
        elements.registryDate.textContent = state.generatedAt
            ? `Artifact: ${formatDateTime(state.generatedAt)}`
            : "Artifact: indexed";
        return;
    }

    if (status === "syncing") {
        elements.registryDot.classList.add("is-syncing");
        elements.registryStatus.textContent = "Syncing registry";
        elements.registryDate.textContent = state.generatedAt
            ? `Artifact: ${formatDateTime(state.generatedAt)}`
            : "Artifact: pending";
        return;
    }

    elements.registryDot.classList.add("is-error");
    elements.registryStatus.textContent = "Registry unavailable";
    elements.registryDate.textContent = detail ? `Error: ${detail}` : "Artifact: unavailable";
}

function updateSyncMeta() {
    if (!state.lastSyncAt) {
        elements.syncMeta.textContent = "Last sync: waiting for first load";
        return;
    }

    const nextSync = state.nextSyncAt ? Math.max(0, Math.round((state.nextSyncAt - Date.now()) / 1000)) : null;
    elements.syncMeta.textContent = nextSync == null
        ? `Last sync: ${timeAgo(state.lastSyncAt)}`
        : `Last sync: ${timeAgo(state.lastSyncAt)} · next refresh in ${nextSync}s`;
}

function updateSurfaceSummary() {
    const runsPart = state.runs.length ? `${state.runs.length} indexed runs` : "no indexed runs yet";
    const paperPart = state.paperAlerts?.has_alerts
        ? `paper attention ${state.paperAlerts.alerts?.length || 0}`
        : (state.paperHealth?.available ? `paper ${state.paperHealth.total_sessions || 0}` : "paper pending");
    const brokerPart = state.brokerHealth?.available ? `broker ${state.brokerHealth.total_sessions || 0}` : "broker pending";
    const pretradePart = state.pretradeIntake?.has_validation
        ? (state.pretradeIntake.accepted ? "pre-trade accepted" : "pre-trade rejected")
        : "pre-trade waiting";

    elements.surfaceSummary.textContent = [runsPart, paperPart, brokerPart, pretradePart].join(" · ");
}

function updateSortHeaders() {
    document.querySelectorAll("th[data-sort]").forEach((header) => {
        const field = header.dataset.sort;
        const active = field === state.sortField;
        header.classList.toggle("is-active", active);
        header.dataset.direction = active ? state.sortDir : "";
        const label = header.textContent.replace(/[↑↓]/g, "").trim();
        header.textContent = active
            ? `${label} ${state.sortDir === "asc" ? "↑" : "↓"}`
            : label;
    });
}

function titleCase(value) {
    return String(value || "")
        .replace(/[_-]+/g, " ")
        .replace(/\s+/g, " ")
        .trim()
        .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatDateTime(value) {
    if (!value) {
        return "-";
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return String(value);
    }

    return new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    }).format(date);
}

function formatPercent(value) {
    if (!isFiniteNumber(value)) {
        return "-";
    }
    return `${value >= 0 ? "" : "-"}${Math.abs(value * 100).toFixed(2)}%`;
}

function formatNumber(value) {
    if (!isFiniteNumber(value)) {
        return "-";
    }
    return new Intl.NumberFormat(undefined, {
        maximumFractionDigits: Math.abs(value) >= 100 ? 0 : 2,
        minimumFractionDigits: Math.abs(value) > 0 && Math.abs(value) < 10 ? 2 : 0,
    }).format(value);
}

function formatCount(value) {
    if (!isFiniteNumber(value)) {
        return "-";
    }
    return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(value);
}

function formatBytes(value) {
    if (!isFiniteNumber(value) || value < 0) {
        return "-";
    }

    if (value < 1024) {
        return `${Math.round(value)} B`;
    }

    const units = ["KB", "MB", "GB", "TB"];
    let size = value / 1024;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex += 1;
    }
    return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[unitIndex]}`;
}

function timeAgo(timestamp) {
    const deltaSeconds = Math.max(0, Math.round((Date.now() - new Date(timestamp).getTime()) / 1000));
    if (deltaSeconds < 5) {
        return "just now";
    }
    if (deltaSeconds < 60) {
        return `${deltaSeconds}s ago`;
    }
    const deltaMinutes = Math.round(deltaSeconds / 60);
    if (deltaMinutes < 60) {
        return `${deltaMinutes}m ago`;
    }
    const deltaHours = Math.round(deltaMinutes / 60);
    if (deltaHours < 24) {
        return `${deltaHours}h ago`;
    }
    const deltaDays = Math.round(deltaHours / 24);
    return `${deltaDays}d ago`;
}

function average(values) {
    if (!values.length) {
        return null;
    }
    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function isFiniteNumber(value) {
    return typeof value === "number" && Number.isFinite(value);
}

function toNumber(value) {
    if (value == null || value === "") {
        return null;
    }
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
}

function toneClass(value, positiveWins) {
    if (!isFiniteNumber(value)) {
        return "";
    }
    if (value === 0) {
        return "tone-neutral";
    }
    if (positiveWins) {
        return value > 0 ? "tone-positive" : "tone-negative";
    }
    return value < 0 ? "tone-positive" : "tone-negative";
}

function launchStatusClass(status) {
    if (status === "succeeded") {
        return "launch-succeeded";
    }
    if (status === "failed") {
        return "launch-failed";
    }
    return "launch-running";
}

function shortCommit(commit) {
    if (!commit) {
        return "";
    }
    return String(commit).slice(0, 7);
}

function normalizePath(value) {
    if (!value) {
        return "";
    }
    return String(value).replace(/\\/g, "/");
}

function toArtifactHref(pathValue) {
    if (!pathValue) {
        return "";
    }

    const normalized = normalizePath(pathValue);
    const marker = "/outputs/";
    const markerIndex = normalized.lastIndexOf(marker);
    if (markerIndex >= 0) {
        return normalized.slice(markerIndex);
    }

    return normalized.startsWith("/") ? normalized : `/${normalized}`;
}

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}
