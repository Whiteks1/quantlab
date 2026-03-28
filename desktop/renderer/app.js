import * as decisionStore from "./modules/decision-store.js";
import {
  absoluteUrl as buildAbsoluteUrl,
  buildRunArtifactHref as buildArtifactHref,
  escapeHtml as escapeMarkup,
  escapeRegex as escapePattern,
  formatBytes as formatByteCount,
  formatCount as formatNumericCount,
  formatDateTime as formatDateTimeValue,
  formatLogPreview as formatLogText,
  formatNumber as formatNumericValue,
  formatPercent as formatPercentValue,
  runtimeChip as renderRuntimeChip,
  shortCommit as shortenCommit,
  stripWrappingQuotes as stripQuotes,
  titleCase as titleCaseValue,
  toneClass as resolveToneClass,
  uniqueRunIds as dedupeRunIds,
} from "./modules/utils.js";
import {
  compareMetric as renderMetricRow,
  renderArtifactsTab as renderArtifactsTabView,
  renderCandidatesTab as renderCandidatesTabView,
  renderCandidateFlags as renderCandidateFlagsView,
  renderCompareTab as renderCompareTabView,
  renderJobTab as renderJobTabView,
  renderPaperOpsTab as renderPaperOpsTabView,
  renderRunTab as renderRunTabView,
  renderSummaryCard as renderSummaryCardView,
} from "./modules/tab-renderers.js";

const CONFIG = {
  runsIndexPath: "/outputs/runs/runs_index.json",
  launchControlPath: "/api/launch-control",
  paperHealthPath: "/api/paper-sessions-health",
  brokerHealthPath: "/api/broker-submissions-health",
  stepbitWorkspacePath: "/api/stepbit-workspace",
  detailArtifacts: ["report.json", "run_report.json"],
  refreshIntervalMs: 15000,
  maxWorklistRuns: 8,
  maxRecentJobs: 4,
  maxLogPreviewChars: 5000,
  maxCandidateCompare: 4,
};

const state = {
  workspace: { status: "starting", serverUrl: null, logs: [], error: null },
  snapshot: null,
  candidatesStore: defaultCandidatesStore(),
  candidatesLoaded: false,
  selectedRunIds: [],
  detailCache: new Map(),
  isSubmittingLaunch: false,
  launchFeedback: "Use deterministic inputs or ask from chat.",
  refreshTimer: null,
  chatMessages: [
    {
      role: "assistant",
      content:
        "QuantLab Desktop now supports a real workflow.\n\nTry:\n- launch run ticker ETH-USD start 2023-01-01 end 2024-01-01\n- open latest run\n- compare selected\n- show artifacts\n- open latest failed launch\n- explain latest failure",
    },
  ],
  tabs: [],
  activeTabId: null,
  paletteOpen: false,
  paletteQuery: "",
};

const elements = {
  runtimeSummary: document.getElementById("runtime-summary"),
  runtimeMeta: document.getElementById("runtime-meta"),
  runtimeChips: document.getElementById("runtime-chips"),
  chatLog: document.getElementById("chat-log"),
  chatForm: document.getElementById("chat-form"),
  chatInput: document.getElementById("chat-input"),
  tabsBar: document.getElementById("tabs-bar"),
  tabContent: document.getElementById("tab-content"),
  topbarTitle: document.getElementById("topbar-title"),
  paletteSearch: document.getElementById("palette-search"),
  paletteInput: document.getElementById("palette-input"),
  runCommand: document.getElementById("run-command"),
  commandPaletteTrigger: document.getElementById("command-palette-trigger"),
  openBrowserRuns: document.getElementById("open-browser-runs"),
  paletteOverlay: document.getElementById("palette-overlay"),
  closePalette: document.getElementById("close-palette"),
  paletteResults: document.getElementById("palette-results"),
  workflowLaunchForm: document.getElementById("workflow-launch-form"),
  workflowLaunchCommand: document.getElementById("workflow-launch-command"),
  workflowRunFields: document.getElementById("workflow-run-fields"),
  workflowSweepFields: document.getElementById("workflow-sweep-fields"),
  workflowLaunchTicker: document.getElementById("workflow-launch-ticker"),
  workflowLaunchStart: document.getElementById("workflow-launch-start"),
  workflowLaunchEnd: document.getElementById("workflow-launch-end"),
  workflowLaunchInterval: document.getElementById("workflow-launch-interval"),
  workflowLaunchCash: document.getElementById("workflow-launch-cash"),
  workflowLaunchPaper: document.getElementById("workflow-launch-paper"),
  workflowLaunchConfigPath: document.getElementById("workflow-launch-config-path"),
  workflowLaunchOutDir: document.getElementById("workflow-launch-out-dir"),
  workflowLaunchMeta: document.getElementById("workflow-launch-meta"),
  workflowLaunchFeedback: document.getElementById("workflow-launch-feedback"),
  workflowLaunchSubmit: document.getElementById("workflow-launch-submit"),
  workflowJobsList: document.getElementById("workflow-jobs-list"),
  workflowRunsMeta: document.getElementById("workflow-runs-meta"),
  workflowRunsList: document.getElementById("workflow-runs-list"),
  workflowOpenCompare: document.getElementById("workflow-open-compare"),
  workflowClearSelection: document.getElementById("workflow-clear-selection"),
};

const paletteActions = [
  ["chat", "Open Chat", "Return focus to the command bus.", () => focusChat()],
  ["launch", "Open Launch", "Open the QuantLab launch surface.", () => openResearchTab("launch", "Launch", "#/launch")],
  ["runs", "Open Runs", "Open the run explorer.", () => openResearchTab("runs", "Runs", "#/")],
  ["candidates", "Open Candidates", "Open the shortlist and baseline surface.", () => openCandidatesTab()],
  ["compare", "Open Compare", "Open a compare tab from selected runs.", () => openCompareSelectionTab()],
  ["shortlist-compare", "Open Shortlist Compare", "Compare the current shortlist or baseline set.", () => openShortlistCompareTab()],
  ["baseline-run", "Open Baseline Run", "Open the current baseline run workspace.", () => openBaselineRunTab()],
  ["ops", "Open Paper Ops", "Open the native operational surface.", () => openPaperOpsTab()],
  ["latest-run", "Open Latest Run", "Open the latest run detail.", () => openLatestRunTab()],
  ["latest-failed", "Open Latest Failed Launch", "Review the most recent failed launch job.", () => openLatestFailedLaunchTab()],
  ["explain-failure", "Explain Latest Failure", "Summarize the latest failed launch from stderr and job state.", () => explainLatestFailureInChat()],
  ["artifacts", "Show Artifacts", "Open artifacts for the selected or latest run.", () => openArtifactsForPreferredRun()],
  ["runtime", "Show Runtime Status", "Summarize runtime health in chat.", () => summarizeRuntimeInChat()],
].map(([id, label, description, run]) => ({ id, label, description, run }));

document.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  renderAll();
  try {
    state.candidatesStore = normalizeCandidatesStore(await window.quantlabDesktop.getCandidatesStore());
  } catch (_error) {
    state.candidatesStore = defaultCandidatesStore();
  } finally {
    state.candidatesLoaded = true;
  }
  const initialState = await window.quantlabDesktop.getWorkspaceState();
  state.workspace = initialState;
  renderWorkspaceState();
  renderWorkflow();
  window.quantlabDesktop.onWorkspaceState((payload) => {
    state.workspace = payload;
    renderWorkspaceState();
    if (payload.serverUrl) ensureRefreshLoop();
  });
  if (initialState.serverUrl) ensureRefreshLoop();
});

window.addEventListener("beforeunload", () => {
  if (state.refreshTimer) window.clearInterval(state.refreshTimer);
});

function bindEvents() {
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.action;
      if (action === "open-chat") focusChat();
      if (action === "open-launch") openResearchTab("launch", "Launch", "#/launch");
      if (action === "open-runs") openResearchTab("runs", "Runs", "#/");
      if (action === "open-candidates") openCandidatesTab();
      if (action === "open-compare") openCompareSelectionTab();
      if (action === "open-ops") openPaperOpsTab();
    });
  });
  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
      const prompt = button.dataset.prompt || "";
      elements.chatInput.value = prompt;
      handleChatPrompt(prompt);
    });
  });
  elements.chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const prompt = elements.chatInput.value.trim();
    if (!prompt) return;
    handleChatPrompt(prompt);
    elements.chatInput.value = "";
  });
  elements.runCommand.addEventListener("click", () => {
    const prompt = elements.paletteInput.value.trim();
    if (!prompt) return;
    handleChatPrompt(prompt);
  });
  elements.commandPaletteTrigger.addEventListener("click", () => {
    state.paletteOpen = true;
    state.paletteQuery = "";
    renderPalette();
    window.setTimeout(() => elements.paletteSearch.focus(), 0);
  });
  elements.closePalette.addEventListener("click", () => {
    state.paletteOpen = false;
    renderPalette();
  });
  elements.paletteSearch.addEventListener("input", () => {
    state.paletteQuery = elements.paletteSearch.value || "";
    renderPalette();
  });
  elements.openBrowserRuns.addEventListener("click", () => {
    const url = getBrowserUrlForActiveContext();
    if (url) window.quantlabDesktop.openExternal(url);
  });
  elements.workflowLaunchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = buildLaunchPayloadFromForm();
    if (payload) await submitLaunchRequest(payload, "form");
  });
  elements.workflowLaunchCommand.addEventListener("change", renderWorkflow);
  elements.workflowOpenCompare.addEventListener("click", () => openCompareSelectionTab());
  elements.workflowClearSelection.addEventListener("click", () => {
    state.selectedRunIds = [];
    renderWorkflow();
  });
  document.addEventListener("keydown", (event) => {
    const isModifierPressed = event.ctrlKey || event.metaKey;
    if (isModifierPressed && event.key.toLowerCase() === "k") {
      event.preventDefault();
      state.paletteOpen = !state.paletteOpen;
      if (!state.paletteOpen) state.paletteQuery = "";
      renderPalette();
      if (state.paletteOpen) window.setTimeout(() => elements.paletteSearch.focus(), 0);
      return;
    }
    if (event.key === "Escape" && state.paletteOpen) {
      state.paletteOpen = false;
      state.paletteQuery = "";
      renderPalette();
    }
  });
}

function ensureRefreshLoop() {
  refreshSnapshot();
  if (!state.refreshTimer) state.refreshTimer = window.setInterval(refreshSnapshot, CONFIG.refreshIntervalMs);
}

async function refreshSnapshot() {
  if (!state.workspace.serverUrl) return;
  try {
    const runsRegistry = await window.quantlabDesktop.requestJson(CONFIG.runsIndexPath);
    state.detailCache.clear();
    const extra = await Promise.allSettled([
      window.quantlabDesktop.requestJson(CONFIG.launchControlPath),
      window.quantlabDesktop.requestJson(CONFIG.paperHealthPath),
      window.quantlabDesktop.requestJson(CONFIG.brokerHealthPath),
      window.quantlabDesktop.requestJson(CONFIG.stepbitWorkspacePath),
    ]);
    state.snapshot = {
      runsRegistry,
      launchControl: extra[0].status === "fulfilled" ? extra[0].value : state.snapshot?.launchControl || null,
      paperHealth: extra[1].status === "fulfilled" ? extra[1].value : state.snapshot?.paperHealth || null,
      brokerHealth: extra[2].status === "fulfilled" ? extra[2].value : state.snapshot?.brokerHealth || null,
      stepbitWorkspace: extra[3].status === "fulfilled" ? extra[3].value : state.snapshot?.stepbitWorkspace || null,
    };
    const validIds = new Set(getRuns().map((run) => run.run_id));
    state.selectedRunIds = state.selectedRunIds.filter((runId) => validIds.has(runId));
    renderWorkspaceState();
    renderWorkflow();
    refreshLiveJobTabs();
    rerenderContextualTabs();
  } catch (_error) {
    // Keep the shell usable even if optional surfaces are down.
  }
}

function renderAll() {
  renderChat();
  renderTabs();
  renderPalette();
  renderWorkflow();
}

function renderWorkspaceState() {
  const { status, serverUrl, error } = state.workspace;
  const runs = getRuns();
  const stepbit = state.snapshot?.stepbitWorkspace?.live_urls || {};
  const paperCount = state.snapshot?.paperHealth?.total_sessions || 0;
  const brokerCount = state.snapshot?.brokerHealth?.total_sessions || 0;
  elements.runtimeSummary.textContent = status === "ready"
    ? "QuantLab research surface ready"
    : status === "starting"
    ? "Starting local research surface"
    : status === "stopped"
    ? "Research surface stopped"
    : "Research surface unavailable";
  elements.runtimeMeta.textContent = error
    ? error
    : serverUrl
    ? `${serverUrl}/research_ui/index.html`
    : "Waiting for localhost server URL.";
  elements.runtimeChips.innerHTML = [
    runtimeChip("QuantLab", status === "ready" ? "up" : status === "starting" ? "starting" : "down", status === "ready" ? "up" : status === "starting" ? "warn" : "down"),
    runtimeChip("Runs", `${runs.length} indexed`, runs.length ? "up" : "warn"),
    runtimeChip("Paper", String(paperCount), paperCount ? "up" : "warn"),
    runtimeChip("Broker", String(brokerCount), brokerCount ? "up" : "warn"),
    runtimeChip("Stepbit app", stepbit.frontend_reachable ? "up" : "down", stepbit.frontend_reachable ? "up" : "down"),
    runtimeChip("Stepbit core", stepbit.core_ready ? "ready" : stepbit.core_reachable ? "up" : "down", stepbit.core_ready ? "up" : stepbit.core_reachable ? "warn" : "down"),
  ].join("");
}

function renderChat() {
  elements.chatLog.innerHTML = state.chatMessages.map((message) => `
    <article class="message ${message.role}">
      <div class="message-role">${escapeHtml(message.role)}</div>
      <div class="message-body">${escapeHtml(message.content)}</div>
    </article>
  `).join("");
  elements.chatLog.scrollTop = elements.chatLog.scrollHeight;
}

function renderTabs() {
  if (!state.tabs.length) {
    elements.tabsBar.innerHTML = "";
    elements.tabContent.innerHTML = `
      <div class="tab-placeholder">
        No context tab is open yet.

        Use chat, quick command, or the workflow panel to launch work, open runs, compare candidates, or inspect artifacts.
      </div>
    `;
    elements.topbarTitle.textContent = "Chat";
    syncNav("chat");
    return;
  }
  elements.tabsBar.innerHTML = state.tabs.map((tab) => `
    <button class="tab-pill ${tab.id === state.activeTabId ? "is-active" : ""}" data-tab-id="${escapeHtml(tab.id)}" type="button">
      <span>${escapeHtml(tab.title)}</span>
      <span class="tab-close" data-close-tab="${escapeHtml(tab.id)}">×</span>
    </button>
  `).join("");
  const activeTab = state.tabs.find((tab) => tab.id === state.activeTabId) || state.tabs[0];
  state.activeTabId = activeTab.id;
  elements.topbarTitle.textContent = activeTab.title;
  syncNav(activeTab.navKind || activeTab.kind);
  if (activeTab.kind === "iframe") {
    elements.tabContent.innerHTML = `<iframe class="tab-frame" src="${escapeHtml(activeTab.url)}" title="${escapeHtml(activeTab.title)}"></iframe>`;
  } else if (activeTab.kind === "run") {
    elements.tabContent.innerHTML = renderRunTab(activeTab);
  } else if (activeTab.kind === "compare") {
    elements.tabContent.innerHTML = renderCompareTab(activeTab);
  } else if (activeTab.kind === "artifacts") {
    elements.tabContent.innerHTML = renderArtifactsTab(activeTab);
  } else if (activeTab.kind === "candidates") {
    elements.tabContent.innerHTML = renderCandidatesTab(activeTab);
  } else if (activeTab.kind === "paper") {
    elements.tabContent.innerHTML = renderPaperOpsTab(activeTab);
  } else if (activeTab.kind === "job") {
    elements.tabContent.innerHTML = renderJobTab(activeTab);
  } else {
    elements.tabContent.innerHTML = `<div class="tab-placeholder">${escapeHtml(activeTab.content || "")}</div>`;
  }
  bindTabChromeEvents();
  bindTabContentEvents(activeTab);
}

function renderPalette() {
  elements.paletteOverlay.classList.toggle("hidden", !state.paletteOpen);
  if (!state.paletteOpen) return;
  const query = state.paletteQuery.trim().toLowerCase();
  if (elements.paletteSearch.value !== state.paletteQuery) {
    elements.paletteSearch.value = state.paletteQuery;
  }
  const visibleActions = paletteActions.filter((action) => {
    if (!query) return true;
    return `${action.label} ${action.description}`.toLowerCase().includes(query);
  });
  elements.paletteResults.innerHTML = visibleActions.map((action) => `
    <button class="palette-item" data-palette-action="${escapeHtml(action.id)}" type="button">
      <strong>${escapeHtml(action.label)}</strong>
      <span>${escapeHtml(action.description)}</span>
    </button>
  `).join("");
  if (!visibleActions.length) {
    elements.paletteResults.innerHTML = `<div class="empty-state">No matching action. Try shortlist, baseline, compare, or paper.</div>`;
  }
  elements.paletteResults.querySelectorAll("[data-palette-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = paletteActions.find((entry) => entry.id === button.dataset.paletteAction);
      if (!action) return;
      action.run();
      state.paletteOpen = false;
      state.paletteQuery = "";
      renderPalette();
    });
  });
}

function renderWorkflow() {
  const command = elements.workflowLaunchCommand.value || "run";
  const isRun = command === "run";
  elements.workflowRunFields.classList.toggle("hidden", !isRun);
  elements.workflowSweepFields.classList.toggle("hidden", isRun);
  elements.workflowLaunchSubmit.disabled = state.isSubmittingLaunch;
  elements.workflowLaunchSubmit.textContent = state.isSubmittingLaunch ? "Launching..." : "Launch in QuantLab";
  elements.workflowLaunchFeedback.textContent = state.launchFeedback;

  const jobs = Array.isArray(state.snapshot?.launchControl?.jobs) ? state.snapshot.launchControl.jobs : [];
  elements.workflowLaunchMeta.textContent = jobs.length
    ? `${jobs.length} tracked jobs · latest ${titleCase(jobs[0].status || "unknown")}`
    : "No launch jobs yet";
  renderJobList(jobs);

  const runs = getRuns();
  const selectedCount = state.selectedRunIds.length;
  const shortlistCount = getShortlistRunIds().length;
  const candidateCount = getCandidateEntries().length;
  elements.workflowRunsMeta.textContent = runs.length
    ? `${Math.min(CONFIG.maxWorklistRuns, runs.length)} of ${runs.length} indexed runs · ${selectedCount} selected · ${candidateCount} candidates · ${shortlistCount} shortlisted`
    : "No runs indexed yet";
  elements.workflowOpenCompare.disabled = selectedCount < 2;
  renderRunsWorklist(runs.slice(0, CONFIG.maxWorklistRuns));
}

function renderJobList(jobs) {
  if (!jobs.length) {
    elements.workflowJobsList.innerHTML = `<div class="empty-state">Launches from the shell or browser surface will appear here.</div>`;
    return;
  }
  elements.workflowJobsList.innerHTML = jobs.slice(0, CONFIG.maxRecentJobs).map((job) => `
    <article class="job-card">
      <div class="job-top">
        <div class="job-name">
          <strong>${escapeHtml(titleCase(job.command || "unknown"))}</strong>
          <span class="job-meta">${escapeHtml(job.request_id || "-")}</span>
        </div>
        <span class="job-status ${escapeHtml(job.status || "unknown")}">${escapeHtml(titleCase(job.status || "unknown"))}</span>
      </div>
      <div>${escapeHtml(job.summary || "-")}</div>
      <div class="job-meta">${escapeHtml(formatDateTime(job.started_at))}${job.ended_at ? ` · ended ${escapeHtml(formatDateTime(job.ended_at))}` : " · running"}</div>
      <div class="workflow-actions">
        <button class="ghost-btn" type="button" data-open-job="${escapeHtml(job.request_id || "")}">Review job</button>
        ${job.run_id ? `<button class="ghost-btn" type="button" data-open-run="${escapeHtml(job.run_id)}">Open run</button>` : ""}
        ${job.artifacts_href ? `<button class="ghost-btn" type="button" data-open-job-artifacts="${escapeHtml(job.request_id || "")}">Artifacts</button>` : ""}
      </div>
    </article>
  `).join("");
  elements.workflowJobsList.querySelectorAll("[data-open-job]").forEach((button) => {
    button.addEventListener("click", () => openJobTab(button.dataset.openJob));
  });
  elements.workflowJobsList.querySelectorAll("[data-open-run]").forEach((button) => {
    button.addEventListener("click", () => openRunDetailTab(button.dataset.openRun));
  });
  elements.workflowJobsList.querySelectorAll("[data-open-job-artifacts]").forEach((button) => {
    button.addEventListener("click", () => openArtifactsForJob(button.dataset.openJobArtifacts));
  });
}

function renderRunsWorklist(runs) {
  if (!runs.length) {
    elements.workflowRunsList.innerHTML = `<div class="empty-state">The run index is still empty. Launch a run or wait for artifacts to appear.</div>`;
    return;
  }
  elements.workflowRunsList.innerHTML = runs.map((run) => {
    const selected = state.selectedRunIds.includes(run.run_id);
    const disableSelection = !selected && state.selectedRunIds.length >= 4;
    return `
      <article class="run-row">
        <div class="run-row-top">
          <div class="run-row-title">
            <strong>${escapeHtml(run.run_id)}</strong>
            <div class="run-row-meta">
              <span>${escapeHtml(titleCase(run.mode || "unknown"))}</span>
              <span>${escapeHtml(run.ticker || "-")}</span>
              <span>${escapeHtml(formatDateTime(run.created_at))}</span>
            </div>
          </div>
          <span class="mode-chip">${escapeHtml(shortCommit(run.git_commit) || "no commit")}</span>
        </div>
        <div class="run-row-metrics">
          <span class="metric-chip ${toneClass(run.total_return, true)}">Return ${formatPercent(run.total_return)}</span>
          <span class="metric-chip">Sharpe ${formatNumber(run.sharpe_simple)}</span>
          <span class="metric-chip ${toneClass(run.max_drawdown, false)}">Drawdown ${formatPercent(run.max_drawdown)}</span>
          <span class="metric-chip">Trades ${formatCount(run.trades)}</span>
        </div>
        <div class="run-row-flags">
          ${renderCandidateFlags(run.run_id)}
        </div>
        <div class="run-row-actions">
          <label class="select-run">
            <input type="checkbox" data-select-run="${escapeHtml(run.run_id)}" ${selected ? "checked" : ""} ${disableSelection ? "disabled" : ""}>
            <span>Select</span>
          </label>
          <button class="ghost-btn" type="button" data-open-run="${escapeHtml(run.run_id)}">Open run</button>
          <button class="ghost-btn" type="button" data-toggle-candidate="${escapeHtml(run.run_id)}">${isCandidateRun(run.run_id) ? "Unmark candidate" : "Mark candidate"}</button>
          <button class="ghost-btn" type="button" data-open-artifacts="${escapeHtml(run.run_id)}">Artifacts</button>
        </div>
      </article>
    `;
  }).join("");
  elements.workflowRunsList.querySelectorAll("[data-select-run]").forEach((input) => {
    input.addEventListener("change", () => toggleRunSelection(input.dataset.selectRun, input.checked));
  });
  elements.workflowRunsList.querySelectorAll("[data-open-run]").forEach((button) => {
    button.addEventListener("click", () => openRunDetailTab(button.dataset.openRun));
  });
  elements.workflowRunsList.querySelectorAll("[data-toggle-candidate]").forEach((button) => {
    button.addEventListener("click", () => toggleCandidate(button.dataset.toggleCandidate));
  });
  elements.workflowRunsList.querySelectorAll("[data-open-artifacts]").forEach((button) => {
    button.addEventListener("click", () => openArtifactsTabForRun(button.dataset.openArtifacts));
  });
}

function bindTabChromeEvents() {
  elements.tabsBar.querySelectorAll("[data-tab-id]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeTabId = button.dataset.tabId;
      renderTabs();
    });
  });
  elements.tabsBar.querySelectorAll("[data-close-tab]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      closeTab(button.dataset.closeTab);
    });
  });
}

function bindTabContentEvents(tab) {
  if (tab.kind === "run") {
    bindRunContextActions(elements.tabContent, tab.runId);
  }
  if (tab.kind === "compare") {
    elements.tabContent.querySelectorAll("[data-open-run]").forEach((button) => {
      button.addEventListener("click", () => openRunDetailTab(button.dataset.openRun));
    });
    elements.tabContent.querySelectorAll("[data-open-artifacts]").forEach((button) => {
      button.addEventListener("click", () => openArtifactsTabForRun(button.dataset.openArtifacts));
    });
    elements.tabContent.querySelectorAll("[data-compare-rank]").forEach((button) => {
      button.addEventListener("click", () => {
        upsertTab({ id: tab.id, rankMetric: button.dataset.compareRank });
      });
    });
    elements.tabContent.querySelectorAll("[data-mark-candidate]").forEach((button) => {
      button.addEventListener("click", () => toggleCandidate(button.dataset.markCandidate));
    });
    elements.tabContent.querySelectorAll("[data-shortlist-run]").forEach((button) => {
      button.addEventListener("click", () => toggleShortlist(button.dataset.shortlistRun));
    });
    elements.tabContent.querySelectorAll("[data-set-baseline]").forEach((button) => {
      button.addEventListener("click", () => setBaseline(button.dataset.setBaseline));
    });
  }
  if (tab.kind === "artifacts") {
    elements.tabContent.querySelectorAll("[data-open-external]").forEach((button) => {
      button.addEventListener("click", () => {
        const url = absoluteUrl(button.dataset.openExternal);
        if (url) window.quantlabDesktop.openExternal(url);
      });
    });
    elements.tabContent.querySelectorAll("[data-open-path]").forEach((button) => {
      button.addEventListener("click", () => {
        if (button.dataset.openPath) window.quantlabDesktop.openPath(button.dataset.openPath);
      });
    });
    elements.tabContent.querySelectorAll("[data-open-run]").forEach((button) => {
      button.addEventListener("click", () => openRunDetailTab(button.dataset.openRun));
    });
    bindRunContextActions(elements.tabContent, tab.runId);
  }
  if (tab.kind === "candidates") {
    elements.tabContent.querySelectorAll("[data-candidates-filter]").forEach((button) => {
      button.addEventListener("click", () => upsertTab({ id: tab.id, filter: button.dataset.candidatesFilter }));
    });
    elements.tabContent.querySelectorAll("[data-open-run]").forEach((button) => {
      button.addEventListener("click", () => openRunDetailTab(button.dataset.openRun));
    });
    elements.tabContent.querySelectorAll("[data-open-artifacts]").forEach((button) => {
      button.addEventListener("click", () => openArtifactsTabForRun(button.dataset.openArtifacts));
    });
    elements.tabContent.querySelectorAll("[data-mark-candidate]").forEach((button) => {
      button.addEventListener("click", () => toggleCandidate(button.dataset.markCandidate));
    });
    elements.tabContent.querySelectorAll("[data-shortlist-run]").forEach((button) => {
      button.addEventListener("click", () => toggleShortlist(button.dataset.shortlistRun));
    });
    elements.tabContent.querySelectorAll("[data-set-baseline]").forEach((button) => {
      button.addEventListener("click", () => setBaseline(button.dataset.setBaseline));
    });
    elements.tabContent.querySelectorAll("[data-edit-note]").forEach((button) => {
      button.addEventListener("click", () => editCandidateNote(button.dataset.editNote));
    });
    elements.tabContent.querySelectorAll("[data-open-shortlist-compare]").forEach((button) => {
      button.addEventListener("click", () => openShortlistCompareTab());
    });
  }
  if (tab.kind === "paper") {
    elements.tabContent.querySelectorAll("[data-open-job]").forEach((button) => {
      button.addEventListener("click", () => openJobTab(button.dataset.openJob));
    });
    elements.tabContent.querySelectorAll("[data-open-run]").forEach((button) => {
      button.addEventListener("click", () => openRunDetailTab(button.dataset.openRun));
    });
    elements.tabContent.querySelectorAll("[data-open-browser-ops]").forEach((button) => {
      button.addEventListener("click", () => {
        const url = absoluteUrl(button.dataset.openBrowserOps);
        if (url) window.quantlabDesktop.openExternal(url);
      });
    });
  }
  if (tab.kind === "job") {
    elements.tabContent.querySelectorAll("[data-open-run]").forEach((button) => {
      button.addEventListener("click", () => openRunDetailTab(button.dataset.openRun));
    });
    elements.tabContent.querySelectorAll("[data-open-job-artifacts]").forEach((button) => {
      button.addEventListener("click", () => openArtifactsForJob(button.dataset.openJobArtifacts));
    });
    elements.tabContent.querySelectorAll("[data-open-job-link]").forEach((button) => {
      button.addEventListener("click", () => {
        const url = absoluteUrl(button.dataset.openJobLink);
        if (url) window.quantlabDesktop.openExternal(url);
      });
    });
  }
}

function handleChatPrompt(prompt) {
  pushMessage("user", prompt);
  const normalized = prompt.trim().toLowerCase();
  if (normalized.includes("open launch") || normalized === "launch") {
    openResearchTab("launch", "Launch", "#/launch");
    pushMessage("assistant", "Opened the Launch surface inside a desktop tab.");
    return;
  }
  if (normalized.includes("open compare") || normalized === "compare" || normalized.includes("compare selected")) {
    openCompareSelectionTab();
    return;
  }
  if (normalized.includes("open shortlist compare")) {
    openShortlistCompareTab();
    return;
  }
  if (normalized.includes("open candidates") || normalized.includes("open shortlist")) {
    openCandidatesTab();
    pushMessage("assistant", "Opened the candidates and shortlist surface.");
    return;
  }
  if (normalized.includes("open ops") || normalized.includes("paper ops")) {
    openPaperOpsTab();
    pushMessage("assistant", "Opened the native Paper Ops surface.");
    return;
  }
  if (normalized.includes("open runs") || normalized === "runs") {
    openResearchTab("runs", "Runs", "#/");
    pushMessage("assistant", "Opened the run explorer.");
    return;
  }
  if (normalized.includes("open baseline")) {
    openBaselineRunTab();
    return;
  }
  if (normalized.includes("latest run")) {
    openLatestRunTab();
    return;
  }
  if (normalized.includes("latest failed launch") || normalized.includes("latest failed job")) {
    openLatestFailedLaunchTab();
    return;
  }
  if (normalized.includes("explain latest failure") || normalized.includes("explain failure")) {
    explainLatestFailureInChat();
    return;
  }
  if (normalized.startsWith("show artifacts")) {
    const explicitRunId = extractRunIdAfterPrefix(prompt, "show artifacts for");
    explicitRunId ? openArtifactsTabForRun(explicitRunId) : openArtifactsForPreferredRun();
    return;
  }
  if (normalized.includes("show runtime status") || normalized === "status") {
    summarizeRuntimeInChat();
    return;
  }
  if (normalized.startsWith("mark candidate")) {
    const runId = extractRunIdAfterPrefix(prompt, "mark candidate").trim();
    if (!runId) {
      pushMessage("assistant", "Use `mark candidate <run_id>` to promote a run into the shortlist workflow.");
      return;
    }
    toggleCandidate(runId, true);
    return;
  }
  if (normalized.startsWith("mark baseline")) {
    const runId = extractRunIdAfterPrefix(prompt, "mark baseline").trim();
    if (!runId) {
      pushMessage("assistant", "Use `mark baseline <run_id>` to pin the reference run.");
      return;
    }
    setBaseline(runId);
    return;
  }
  const launchRunPayload = parseLaunchRunPrompt(prompt);
  if (launchRunPayload) {
    submitLaunchRequest(launchRunPayload, "chat");
    return;
  }
  const launchSweepPayload = parseLaunchSweepPrompt(prompt);
  if (launchSweepPayload) {
    submitLaunchRequest(launchSweepPayload, "chat");
    return;
  }
  pushMessage("assistant", "This shell now supports real backend-backed actions. Try:\n- launch run ticker ETH-USD start 2023-01-01 end 2024-01-01\n- launch sweep config configs/sweeps/example.yaml\n- open candidates\n- mark candidate <run_id>\n- mark baseline <run_id>\n- open latest run\n- compare selected\n- show artifacts\n- open latest failed launch\n- explain latest failure");
}

async function submitLaunchRequest(payload, source) {
  state.isSubmittingLaunch = true;
  state.launchFeedback = `Submitting ${payload.command} request from ${source}...`;
  renderWorkflow();
  try {
    const result = await window.quantlabDesktop.postJson(CONFIG.launchControlPath, payload);
    state.launchFeedback = result.message || "Launch accepted.";
    await refreshSnapshot();
    openResearchTab("launch", "Launch", "#/launch");
    pushMessage("assistant", `${result.message || "Launch accepted."}\n${summarizeLaunchPayload(payload)}`);
  } catch (error) {
    const message = error.message || "Launch failed.";
    state.launchFeedback = message;
    pushMessage("assistant", message);
  } finally {
    state.isSubmittingLaunch = false;
    renderWorkflow();
  }
}

function summarizeRuntimeInChat() {
  const runs = getRuns();
  const stepbit = state.snapshot?.stepbitWorkspace?.live_urls || {};
  pushMessage("assistant", [
    `QuantLab server: ${state.workspace.status}`,
    `Server URL: ${state.workspace.serverUrl || "pending"}`,
    `Indexed runs: ${runs.length}`,
    `Selected runs: ${state.selectedRunIds.length}`,
    `Candidates: ${getCandidateEntries().length}`,
    `Shortlisted: ${getShortlistRunIds().length}`,
    `Baseline: ${state.candidatesStore.baseline_run_id || "none"}`,
    `Stepbit frontend: ${stepbit.frontend_reachable ? "up" : "down"}`,
    `Stepbit backend: ${stepbit.backend_reachable ? "up" : "down"}`,
    `Stepbit core: ${stepbit.core_ready ? "ready" : stepbit.core_reachable ? "up" : "down"}`,
  ].join("\n"));
}

function focusChat() {
  state.activeTabId = null;
  renderTabs();
  pushMessage("assistant", "Chat stays at the center of the shell. Use it to launch work, open runs, compare, or inspect artifacts.");
}

function openResearchTab(navKind, title, hash) {
  if (!state.workspace.serverUrl) {
    pushMessage("assistant", "The local research surface is still starting. Wait a moment and retry.");
    return;
  }
  const id = `iframe:${hash}`;
  const existing = state.tabs.find((tab) => tab.id === id);
  if (existing) {
    state.activeTabId = existing.id;
    renderTabs();
    return;
  }
  state.tabs.push({ id, kind: "iframe", navKind, title, url: `${state.workspace.serverUrl}/research_ui/index.html${hash}` });
  state.activeTabId = id;
  renderTabs();
}

function openLatestRunTab() {
  const latestRun = getLatestRun();
  if (!latestRun?.run_id) {
    pushMessage("assistant", "No indexed runs are available yet, so there is no latest run to open.");
    return;
  }
  openRunDetailTab(latestRun.run_id);
  pushMessage("assistant", `Opened the latest indexed run: ${latestRun.run_id}.`);
}

async function openRunDetailTab(runId) {
  const run = findRun(runId);
  if (!run) {
    pushMessage("assistant", `Run ${runId} is not present in the current registry snapshot.`);
    return;
  }
  const tabId = `run:${runId}`;
  upsertTab({ id: tabId, kind: "run", navKind: "runs", title: `Run ${run.run_id}`, runId, status: "loading", detail: null, error: null });
  try {
    const detail = await loadRunDetail(runId);
    upsertTab({ id: tabId, kind: "run", navKind: "runs", title: `Run ${run.run_id}`, runId, status: "ready", detail, error: null });
  } catch (error) {
    upsertTab({ id: tabId, kind: "run", navKind: "runs", title: `Run ${run.run_id}`, runId, status: "error", detail: null, error: error.message || "Could not load run detail." });
    pushMessage("assistant", error.message || `Could not load run ${runId}.`);
  }
}

async function openCompareSelectionTab(runIds = state.selectedRunIds, sourceLabel = "selected runs") {
  const selectedRuns = uniqueRunIds(runIds).map(findRun).filter(Boolean);
  if (selectedRuns.length < 2) {
    pushMessage("assistant", "Select 2 to 4 runs in the worklist before opening compare.");
    return;
  }
  const compareSet = selectedRuns.slice(0, CONFIG.maxCandidateCompare);
  const tabId = `compare:${compareSet.map((run) => run.run_id).join("|")}`;
  upsertTab({
    id: tabId,
    kind: "compare",
    navKind: "compare",
    title: `Compare ${compareSet.length} runs`,
    runIds: compareSet.map((run) => run.run_id),
    rankMetric: "sharpe_simple",
    status: "loading",
    detailMap: {},
  });
  try {
    const details = await Promise.all(compareSet.map(async (run) => {
      try {
        const detail = await loadRunDetail(run.run_id);
        return [run.run_id, detail];
      } catch (_error) {
        return [run.run_id, null];
      }
    }));
    upsertTab({
      id: tabId,
      kind: "compare",
      navKind: "compare",
      title: `Compare ${compareSet.length} runs`,
      runIds: compareSet.map((run) => run.run_id),
      rankMetric: "sharpe_simple",
      status: "ready",
      detailMap: Object.fromEntries(details),
    });
  } catch (_error) {
    upsertTab({
      id: tabId,
      kind: "compare",
      navKind: "compare",
      title: `Compare ${compareSet.length} runs`,
      runIds: compareSet.map((run) => run.run_id),
      rankMetric: "sharpe_simple",
      status: "ready",
      detailMap: {},
    });
  }
  pushMessage("assistant", `Opened a compare tab for ${compareSet.length} ${sourceLabel}.`);
}

function openCandidatesTab(filter = "all") {
  upsertTab({
    id: "candidates",
    kind: "candidates",
    navKind: "candidates",
    title: "Candidates",
    filter,
  });
}

function openPaperOpsTab() {
  upsertTab({
    id: "paper-ops",
    kind: "paper",
    navKind: "ops",
    title: "Paper Ops",
  });
}

function openBaselineRunTab() {
  const baselineRunId = state.candidatesStore.baseline_run_id;
  if (!baselineRunId) {
    pushMessage("assistant", "No baseline run is pinned yet.");
    return;
  }
  openRunDetailTab(baselineRunId);
  pushMessage("assistant", `Opened the current baseline run: ${baselineRunId}.`);
}

function openShortlistCompareTab() {
  const runIds = getDecisionCompareRunIds();
  if (runIds.length < 2) {
    pushMessage("assistant", "Shortlist compare needs at least two decision runs across shortlist and baseline.");
    return;
  }
  openCompareSelectionTab(runIds, "decision runs");
}

function openArtifactsForPreferredRun() {
  const selectedRuns = getSelectedRuns();
  if (selectedRuns.length) {
    openArtifactsTabForRun(selectedRuns[0].run_id);
    return;
  }
  const latestRun = getLatestRun();
  if (!latestRun) {
    pushMessage("assistant", "No run is available yet for artifact inspection.");
    return;
  }
  openArtifactsTabForRun(latestRun.run_id);
}

async function openArtifactsTabForRun(runId) {
  const run = findRun(runId);
  if (!run) {
    pushMessage("assistant", `Run ${runId} is not present in the current registry snapshot.`);
    return;
  }
  const tabId = `artifacts:${runId}`;
  upsertTab({ id: tabId, kind: "artifacts", navKind: "runs", title: `Artifacts ${runId}`, runId, status: "loading", detail: null, error: null });
  try {
    const detail = await loadRunDetail(runId);
    upsertTab({ id: tabId, kind: "artifacts", navKind: "runs", title: `Artifacts ${runId}`, runId, status: "ready", detail, error: null });
    pushMessage("assistant", `Opened artifacts for ${runId}.`);
  } catch (error) {
    upsertTab({ id: tabId, kind: "artifacts", navKind: "runs", title: `Artifacts ${runId}`, runId, status: "error", detail: null, error: error.message || "Could not read canonical artifacts." });
    pushMessage("assistant", error.message || `Could not read artifacts for ${runId}.`);
  }
}

async function openJobTab(requestId) {
  const job = findJob(requestId);
  if (!job) {
    pushMessage("assistant", `Launch job ${requestId} is not present in the current snapshot.`);
    return;
  }

  const tabId = `job:${requestId}`;
  upsertTab({
    id: tabId,
    kind: "job",
    navKind: "launch",
    title: `Job ${requestId}`,
    requestId,
    status: "loading",
    job,
    stdoutText: "",
    stderrText: "",
    error: null,
  });

  await refreshJobTab(requestId, job);
}

async function refreshJobTab(requestId, fallbackJob = null, options = {}) {
  const { silent = false } = options;
  const tabId = `job:${requestId}`;
  const job = findJob(requestId) || fallbackJob;
  if (!job) {
    if (!silent) pushMessage("assistant", `Launch job ${requestId} is not present in the current snapshot.`);
    return;
  }

  try {
    const [stdoutText, stderrText] = await Promise.all([
      loadOptionalText(job.stdout_href),
      loadOptionalText(job.stderr_href),
    ]);
    upsertTab({
      id: tabId,
      kind: "job",
      navKind: "launch",
      title: `Job ${requestId}`,
      requestId,
      status: "ready",
      job: findJob(requestId) || job,
      stdoutText,
      stderrText,
      error: null,
    });
    if (!silent) pushMessage("assistant", `Opened launch job ${requestId}.`);
  } catch (error) {
    upsertTab({
      id: tabId,
      kind: "job",
      navKind: "launch",
      title: `Job ${requestId}`,
      requestId,
      status: "error",
      job,
      stdoutText: "",
      stderrText: "",
      error: error.message || "Could not load job logs.",
    });
    if (!silent) pushMessage("assistant", error.message || `Could not load job ${requestId}.`);
  }
}

function openLatestFailedLaunchTab() {
  const job = getLatestFailedJob();
  if (!job) {
    pushMessage("assistant", "No failed launch job is currently available.");
    return;
  }
  openJobTab(job.request_id);
}

async function explainLatestFailureInChat() {
  const job = getLatestFailedJob();
  if (!job) {
    pushMessage("assistant", "No failed launch job is currently available, so there is nothing to explain.");
    return;
  }
  const stderrText = await loadOptionalText(job.stderr_href);
  const explanation = buildFailureExplanation(job, stderrText);
  pushMessage("assistant", explanation);
}

function openArtifactsForJob(requestId) {
  const job = findJob(requestId);
  if (!job) {
    pushMessage("assistant", `Launch job ${requestId} is not present in the current snapshot.`);
    return;
  }
  if (job.run_id) {
    openArtifactsTabForRun(job.run_id);
    return;
  }
  if (job.artifacts_href) {
    const url = absoluteUrl(job.artifacts_href);
    if (url) {
      window.quantlabDesktop.openExternal(url);
      pushMessage("assistant", `Opened artifact folder for job ${requestId} in the browser.`);
      return;
    }
  }
  pushMessage("assistant", `Job ${requestId} does not expose artifacts yet.`);
}

function closeTab(tabId) {
  state.tabs = state.tabs.filter((tab) => tab.id !== tabId);
  if (state.activeTabId === tabId) state.activeTabId = state.tabs[0]?.id || null;
  renderTabs();
}

function syncNav(kind) {
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("is-active"));
  const mapping = { chat: "open-chat", launch: "open-launch", runs: "open-runs", candidates: "open-candidates", compare: "open-compare", ops: "open-ops" };
  const target = document.querySelector(`.nav-item[data-action="${mapping[kind] || "open-chat"}"]`);
  if (target) target.classList.add("is-active");
}

function pushMessage(role, content) {
  state.chatMessages.push({ role, content });
  renderChat();
}

function buildLaunchPayloadFromForm() {
  const command = elements.workflowLaunchCommand.value || "run";
  if (command === "run") {
    const ticker = elements.workflowLaunchTicker.value.trim();
    const start = elements.workflowLaunchStart.value;
    const end = elements.workflowLaunchEnd.value;
    if (!ticker || !start || !end) {
      state.launchFeedback = "Run launches need ticker, start, and end.";
      renderWorkflow();
      return null;
    }
    const params = { ticker, start, end };
    const interval = elements.workflowLaunchInterval.value.trim();
    const initialCash = elements.workflowLaunchCash.value.trim();
    if (interval) params.interval = interval;
    if (initialCash) params.initial_cash = initialCash;
    if (elements.workflowLaunchPaper.checked) params.paper = true;
    return { command, params };
  }
  const configPath = elements.workflowLaunchConfigPath.value.trim();
  if (!configPath) {
    state.launchFeedback = "Sweep launches need config_path.";
    renderWorkflow();
    return null;
  }
  const params = { config_path: configPath };
  const outDir = elements.workflowLaunchOutDir.value.trim();
  if (outDir) params.out_dir = outDir;
  return { command, params };
}

function parseLaunchRunPrompt(prompt) {
  if (!prompt.trim().toLowerCase().startsWith("launch run")) return null;
  const keys = ["ticker", "start", "end", "interval", "cash", "paper"];
  const ticker = extractNamedValue(prompt, "ticker", keys);
  const start = extractNamedValue(prompt, "start", keys);
  const end = extractNamedValue(prompt, "end", keys);
  if (!ticker || !start || !end) return null;
  const params = { ticker, start, end };
  const interval = extractNamedValue(prompt, "interval", keys);
  const cash = extractNamedValue(prompt, "cash", keys);
  if (interval) params.interval = interval;
  if (cash) params.initial_cash = cash;
  if (/\bpaper\b/i.test(prompt)) params.paper = true;
  return { command: "run", params };
}

function parseLaunchSweepPrompt(prompt) {
  if (!prompt.trim().toLowerCase().startsWith("launch sweep")) return null;
  const keys = ["config", "out"];
  const configPath = extractNamedValue(prompt, "config", keys);
  if (!configPath) return null;
  const payload = { command: "sweep", params: { config_path: configPath } };
  const outDir = extractNamedValue(prompt, "out", keys);
  if (outDir) payload.params.out_dir = outDir;
  return payload;
}

function extractNamedValue(prompt, key, knownKeys = []) {
  const otherKeys = knownKeys.filter((candidate) => candidate !== key).map(escapeRegex);
  const boundary = otherKeys.length ? `(?=\\s+(?:${otherKeys.join("|")})\\b|$)` : `(?=$)`;
  const match = String(prompt).match(new RegExp(`${escapeRegex(key)}\\s+(.+?)${boundary}`, "i"));
  return match ? stripWrappingQuotes(match[1].trim()) : "";
}

function extractRunIdAfterPrefix(prompt, prefix) {
  const normalizedPrefix = prefix.trim().toLowerCase();
  const normalized = prompt.trim().toLowerCase();
  if (!normalized.startsWith(normalizedPrefix)) return "";
  return prompt.trim().slice(prefix.length).trim();
}

function renderRunTab(tab) {
  return renderRunTabView(tab, getRendererContext());
}

function renderCompareTab(tab) {
  return renderCompareTabView(tab, getRendererContext());
}

function renderArtifactsTab(tab) {
  return renderArtifactsTabView(tab, getRendererContext());
}

function renderCandidatesTab(tab) {
  return renderCandidatesTabView(tab, getRendererContext());
}

function renderPaperOpsTab() {
  return renderPaperOpsTabView(getRendererContext());
}

function renderJobTab(tab) {
  return renderJobTabView(tab, getRendererContext());
}

function renderSummaryCard(label, value, tone = "") {
  return renderSummaryCardView(label, value, tone);
}

function compareMetric(label, value, extraClass) {
  return renderMetricRow(label, value, extraClass);
}

function getRendererContext() {
  return {
    store: state.candidatesStore,
    snapshot: state.snapshot,
    maxLogPreviewChars: CONFIG.maxLogPreviewChars,
    decision: {
      getCandidateEntry: (store, runId) => decisionStore.getCandidateEntry(store, runId),
      getCandidateEntryResolved: (store, runId, findRunFn) => decisionStore.getCandidateEntryResolved(store, runId, findRunFn),
      getCandidateEntriesResolved: (store, findRunFn) => decisionStore.getCandidateEntriesResolved(store, findRunFn),
      buildMissingCandidateEntry: (runId, findRunFn) => decisionStore.buildMissingCandidateEntry(runId, findRunFn),
      isCandidateRun: (store, runId) => decisionStore.isCandidateRun(store, runId),
      isShortlistedRun: (store, runId) => decisionStore.isShortlistedRun(store, runId),
      isBaselineRun: (store, runId) => decisionStore.isBaselineRun(store, runId),
      summarizeCandidateState: (store, runId) => decisionStore.summarizeCandidateState(store, runId),
    },
    findRun,
    findJob,
    getRuns,
    getJobs,
    getLatestRun,
    buildFailureExplanation,
  };
}

function upsertTab(nextTab) {
  const index = state.tabs.findIndex((tab) => tab.id === nextTab.id);
  if (index >= 0) state.tabs[index] = { ...state.tabs[index], ...nextTab };
  else state.tabs.push(nextTab);
  state.activeTabId = nextTab.id;
  renderTabs();
}

function rerenderContextualTabs() {
  if (state.tabs.some((tab) => ["run", "compare", "artifacts", "candidates", "paper", "job"].includes(tab.kind))) renderTabs();
}

function refreshLiveJobTabs() {
  state.tabs
    .filter((tab) => tab.kind === "job")
    .forEach((tab) => {
      const currentJob = findJob(tab.requestId);
      if (!currentJob) return;
      const statusChanged = tab.job?.status !== currentJob.status;
      const needsLiveRefresh = currentJob.status === "running" || statusChanged;
      if (needsLiveRefresh) {
        refreshJobTab(tab.requestId, currentJob, { silent: true });
      }
    });
}

async function loadRunDetail(runId) {
  if (state.detailCache.has(runId)) return state.detailCache.get(runId);
  const run = findRun(runId);
  if (!run?.path) throw new Error(`Run ${runId} has no accessible artifact path.`);
  let detail = { report: null, reportUrl: null, directoryEntries: [], directoryTruncated: false };
  for (const artifact of CONFIG.detailArtifacts) {
    const href = buildRunArtifactHref(run.path, artifact);
    try {
      const report = await window.quantlabDesktop.requestJson(href);
      detail = { ...detail, report, reportUrl: href };
      break;
    } catch (_error) {
      // Keep trying the remaining artifact names.
    }
  }
  try {
    const listing = await window.quantlabDesktop.listDirectory(run.path, 2);
    detail.directoryEntries = listing.entries || [];
    detail.directoryTruncated = Boolean(listing.truncated);
  } catch (_error) {
    // Directory listing is helpful but optional.
  }
  if (detail.report) {
    state.detailCache.set(runId, detail);
  }
  return detail;
}

function toggleRunSelection(runId, selected) {
  if (!runId) return;
  if (selected) {
    if (!state.selectedRunIds.includes(runId) && state.selectedRunIds.length < 4) state.selectedRunIds = [...state.selectedRunIds, runId];
  } else {
    state.selectedRunIds = state.selectedRunIds.filter((value) => value !== runId);
  }
  renderWorkflow();
}

function getBrowserUrlForActiveContext() {
  if (!state.workspace.serverUrl) return "";
  const activeTab = state.tabs.find((tab) => tab.id === state.activeTabId);
  if (activeTab?.kind === "iframe") return activeTab.url;
  if (activeTab?.kind === "run") return getBrowserUrlForRun(activeTab.runId);
  if (activeTab?.kind === "paper") return `${state.workspace.serverUrl}/research_ui/index.html#/ops`;
  if (activeTab?.kind === "job") return `${state.workspace.serverUrl}/research_ui/index.html#/launch`;
  return `${state.workspace.serverUrl}/research_ui/index.html#/`;
}

function getBrowserUrlForRun(runId) {
  if (!state.workspace.serverUrl || !runId) return "";
  return `${state.workspace.serverUrl}/research_ui/index.html#/run/${encodeURIComponent(runId)}`;
}

function getRuns() {
  return Array.isArray(state.snapshot?.runsRegistry?.runs) ? state.snapshot.runsRegistry.runs : [];
}

function getJobs() {
  return Array.isArray(state.snapshot?.launchControl?.jobs) ? state.snapshot.launchControl.jobs : [];
}

function defaultCandidatesStore() {
  return decisionStore.defaultCandidatesStore();
}

function normalizeCandidatesStore(store) {
  return decisionStore.normalizeCandidatesStore(store);
}

function getLatestRun() {
  return getRuns()[0] || null;
}

function getLatestFailedJob() {
  return getJobs().find((job) => job.status === "failed") || null;
}

function getSelectedRuns() {
  return state.selectedRunIds.map(findRun).filter(Boolean);
}

function getCandidateEntries() {
  return decisionStore.getCandidateEntries(state.candidatesStore);
}

function getCandidateEntry(runId) {
  return decisionStore.getCandidateEntry(state.candidatesStore, runId);
}

function getCandidateEntryResolved(runId) {
  return decisionStore.getCandidateEntryResolved(state.candidatesStore, runId, findRun);
}

function getCandidateEntriesResolved() {
  return decisionStore.getCandidateEntriesResolved(state.candidatesStore, findRun);
}

function buildMissingCandidateEntry(runId) {
  return decisionStore.buildMissingCandidateEntry(runId, findRun);
}

function isCandidateRun(runId) {
  return decisionStore.isCandidateRun(state.candidatesStore, runId);
}

function isShortlistedRun(runId) {
  return decisionStore.isShortlistedRun(state.candidatesStore, runId);
}

function isBaselineRun(runId) {
  return decisionStore.isBaselineRun(state.candidatesStore, runId);
}

function getShortlistRunIds() {
  return decisionStore.getShortlistRunIds(state.candidatesStore, findRun);
}

function getDecisionCompareRunIds() {
  return decisionStore.getDecisionCompareRunIds(state.candidatesStore, findRun, uniqueRunIds, CONFIG.maxCandidateCompare);
}

function findRun(runId) {
  return getRuns().find((run) => run.run_id === runId) || null;
}

function findJob(requestId) {
  return getJobs().find((job) => job.request_id === requestId) || null;
}

async function saveCandidatesStore(nextStore, message = "") {
  try {
    state.candidatesStore = normalizeCandidatesStore(await window.quantlabDesktop.saveCandidatesStore(nextStore));
    renderWorkflow();
    rerenderContextualTabs();
    if (message) pushMessage("assistant", message);
  } catch (error) {
    pushMessage("assistant", error.message || "Could not persist the candidates store.");
  }
}

async function toggleCandidate(runId, forceValue = null) {
  const run = findRun(runId);
  if (!run) {
    pushMessage("assistant", `Run ${runId} is not present in the registry snapshot.`);
    return;
  }
  const existing = getCandidateEntry(runId);
  const shouldExist = forceValue === null ? !existing : Boolean(forceValue);
  const entries = getCandidateEntries().filter((entry) => entry.run_id !== runId);
  if (shouldExist) {
    entries.push({
      run_id: runId,
      note: existing?.note || "",
      shortlisted: existing?.shortlisted || false,
      created_at: existing?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  }
  const nextStore = {
    ...state.candidatesStore,
    entries,
    baseline_run_id: shouldExist || state.candidatesStore.baseline_run_id !== runId ? state.candidatesStore.baseline_run_id : null,
  };
  await saveCandidatesStore(nextStore, shouldExist ? `Marked ${runId} as a candidate.` : `Removed ${runId} from candidates.`);
}

async function toggleShortlist(runId) {
  const run = findRun(runId);
  if (!run) {
    pushMessage("assistant", `Run ${runId} is not present in the registry snapshot.`);
    return;
  }
  const existing = getCandidateEntry(runId);
  const nextEntry = {
    run_id: runId,
    note: existing?.note || "",
    shortlisted: !existing?.shortlisted,
    created_at: existing?.created_at || new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  const entries = getCandidateEntries().filter((entry) => entry.run_id !== runId);
  entries.push(nextEntry);
  await saveCandidatesStore(
    {
      ...state.candidatesStore,
      entries,
    },
    nextEntry.shortlisted ? `Added ${runId} to the shortlist.` : `Removed ${runId} from the shortlist.`,
  );
}

async function setBaseline(runId) {
  const run = findRun(runId);
  if (!run) {
    pushMessage("assistant", `Run ${runId} is not present in the registry snapshot.`);
    return;
  }
  const nextBaseline = state.candidatesStore.baseline_run_id === runId ? null : runId;
  let entries = getCandidateEntries().filter((entry) => entry.run_id !== runId);
  const existing = getCandidateEntry(runId);
  if (nextBaseline) {
    entries.push({
      run_id: runId,
      note: existing?.note || "",
      shortlisted: existing?.shortlisted || false,
      created_at: existing?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  } else if (existing) {
    entries.push(existing);
  }
  await saveCandidatesStore(
    {
      ...state.candidatesStore,
      baseline_run_id: nextBaseline,
      entries,
    },
    nextBaseline ? `Pinned ${runId} as the current baseline.` : `Cleared the baseline reference.`,
  );
}

async function editCandidateNote(runId) {
  const run = findRun(runId);
  if (!run) {
    pushMessage("assistant", `Run ${runId} is not present in the registry snapshot.`);
    return;
  }
  const existing = getCandidateEntry(runId);
  const nextNote = window.prompt(`Candidate note for ${runId}`, existing?.note || "");
  if (nextNote === null) return;
  const entries = getCandidateEntries().filter((entry) => entry.run_id !== runId);
  entries.push({
    run_id: runId,
    note: nextNote.trim(),
    shortlisted: existing?.shortlisted || false,
    created_at: existing?.created_at || new Date().toISOString(),
    updated_at: new Date().toISOString(),
  });
  await saveCandidatesStore(
    {
      ...state.candidatesStore,
      entries,
    },
    nextNote.trim() ? `Updated the note for ${runId}.` : `Cleared the note for ${runId}.`,
  );
}

function summarizeCandidateState(runId) {
  return decisionStore.summarizeCandidateState(state.candidatesStore, runId);
}

function renderCandidateFlags(runId) {
  return renderCandidateFlagsView(state.candidatesStore, runId, decisionStore);
}

function bindRunContextActions(container, runId) {
  container.querySelectorAll("[data-open-artifacts]").forEach((button) => {
    button.addEventListener("click", () => openArtifactsTabForRun(button.dataset.openArtifacts || runId));
  });
  container.querySelectorAll("[data-mark-candidate]").forEach((button) => {
    button.addEventListener("click", () => toggleCandidate(button.dataset.markCandidate));
  });
  container.querySelectorAll("[data-shortlist-run]").forEach((button) => {
    button.addEventListener("click", () => toggleShortlist(button.dataset.shortlistRun));
  });
  container.querySelectorAll("[data-set-baseline]").forEach((button) => {
    button.addEventListener("click", () => setBaseline(button.dataset.setBaseline));
  });
  container.querySelectorAll("[data-edit-note]").forEach((button) => {
    button.addEventListener("click", () => editCandidateNote(button.dataset.editNote));
  });
  container.querySelectorAll("[data-open-browser-run]").forEach((button) => {
    button.addEventListener("click", () => {
      const url = getBrowserUrlForRun(button.dataset.openBrowserRun || runId);
      if (url) window.quantlabDesktop.openExternal(url);
    });
  });
}

function uniqueRunIds(runIds) {
  return dedupeRunIds(runIds);
}

function summarizeLaunchPayload(payload) {
  return payload.command === "run"
    ? `Run ${payload.params.ticker} ${payload.params.start} -> ${payload.params.end}`
    : `Sweep ${payload.params.config_path}`;
}

function buildRunArtifactHref(runPath, fileName) {
  return buildArtifactHref(runPath, fileName);
}

function absoluteUrl(relativeOrUrl) {
  return buildAbsoluteUrl(state.workspace.serverUrl, relativeOrUrl);
}

async function loadOptionalText(relativePath) {
  if (!relativePath) return "";
  try {
    return await window.quantlabDesktop.requestText(relativePath);
  } catch (_error) {
    return "";
  }
}

function buildFailureExplanation(job, stderrText) {
  if (!job) return "No launch job information is available.";
  if (job.status !== "failed") {
    return job.status === "succeeded"
      ? "This launch completed successfully. Use the run tab or artifacts tab for deeper inspection."
      : "This launch is still in progress, so a failure explanation is not available yet.";
  }
  const stderr = String(stderrText || job.error_message || "").trim();
  const lowered = stderr.toLowerCase();
  let likelyCause = "QuantLab reported a generic runtime failure. Review stderr for the exact failing step.";
  if (lowered.includes("ticker") || lowered.includes("start") || lowered.includes("end")) {
    likelyCause = "The failure looks related to missing or invalid launch parameters.";
  } else if (lowered.includes("config") || lowered.includes("yaml")) {
    likelyCause = "The failure looks related to a missing or invalid sweep configuration file.";
  } else if (lowered.includes("module") || lowered.includes("import")) {
    likelyCause = "The failure looks related to a Python environment or dependency import problem.";
  } else if (lowered.includes("permission") || lowered.includes("access")) {
    likelyCause = "The failure looks related to file-system permissions or path access.";
  } else if (lowered.includes("file not found") || lowered.includes("no such file")) {
    likelyCause = "The failure looks related to a missing file or artifact path.";
  }
  const lastLine = stderr ? stderr.split(/\r?\n/).filter(Boolean).slice(-1)[0] : "";
  return [likelyCause, lastLine ? `Last stderr line: ${lastLine}` : "", job.error_message ? `Reported error: ${job.error_message}` : ""]
    .filter(Boolean)
    .join("\n");
}

function formatLogPreview(text) {
  return formatLogText(text, CONFIG.maxLogPreviewChars);
}

function runtimeChip(label, value, tone) {
  return renderRuntimeChip(label, value, tone);
}

function titleCase(value) {
  return titleCaseValue(value);
}

function shortCommit(value) {
  return shortenCommit(value);
}

function formatDateTime(value) {
  return formatDateTimeValue(value);
}

function formatPercent(value) {
  return formatPercentValue(value);
}

function formatNumber(value) {
  return formatNumericValue(value);
}

function formatCount(value) {
  return formatNumericCount(value);
}

function formatBytes(value) {
  return formatByteCount(value);
}

function toneClass(value, higherIsBetter) {
  return resolveToneClass(value, higherIsBetter);
}

function stripWrappingQuotes(value) {
  return stripQuotes(value);
}

function escapeRegex(value) {
  return escapePattern(value);
}

function escapeHtml(value) {
  return escapeMarkup(value);
}
