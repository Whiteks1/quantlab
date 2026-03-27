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
};

const state = {
  workspace: { status: "starting", serverUrl: null, logs: [], error: null },
  snapshot: null,
  selectedRunIds: [],
  detailCache: new Map(),
  isSubmittingLaunch: false,
  launchFeedback: "Use deterministic inputs or ask from chat.",
  refreshTimer: null,
  chatMessages: [
    {
      role: "assistant",
      content:
        "QuantLab Desktop now supports a real workflow.\n\nTry:\n- launch run ticker ETH-USD start 2023-01-01 end 2024-01-01\n- open latest run\n- compare selected\n- show artifacts\n- show runtime status",
    },
  ],
  tabs: [],
  activeTabId: null,
  paletteOpen: false,
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
  ["compare", "Open Compare", "Open a compare tab from selected runs.", () => openCompareSelectionTab()],
  ["ops", "Open Paper Ops", "Open operational surfaces.", () => openResearchTab("ops", "Paper Ops", "#/ops")],
  ["latest-run", "Open Latest Run", "Open the latest run detail.", () => openLatestRunTab()],
  ["artifacts", "Show Artifacts", "Open artifacts for the selected or latest run.", () => openArtifactsForPreferredRun()],
  ["runtime", "Show Runtime Status", "Summarize runtime health in chat.", () => summarizeRuntimeInChat()],
].map(([id, label, description, run]) => ({ id, label, description, run }));

document.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  renderAll();
  const initialState = await window.quantlabDesktop.getWorkspaceState();
  state.workspace = initialState;
  renderWorkspaceState();
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
      if (action === "open-compare") openCompareSelectionTab();
      if (action === "open-ops") openResearchTab("ops", "Paper Ops", "#/ops");
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
    renderPalette();
  });
  elements.closePalette.addEventListener("click", () => {
    state.paletteOpen = false;
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
}

function ensureRefreshLoop() {
  refreshSnapshot();
  if (!state.refreshTimer) state.refreshTimer = window.setInterval(refreshSnapshot, CONFIG.refreshIntervalMs);
}

async function refreshSnapshot() {
  if (!state.workspace.serverUrl) return;
  try {
    const runsRegistry = await window.quantlabDesktop.requestJson(CONFIG.runsIndexPath);
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
  } else if (activeTab.kind === "compare") {
    elements.tabContent.innerHTML = renderCompareTab(activeTab);
  } else if (activeTab.kind === "artifacts") {
    elements.tabContent.innerHTML = renderArtifactsTab(activeTab);
  } else {
    elements.tabContent.innerHTML = `<div class="tab-placeholder">${escapeHtml(activeTab.content || "")}</div>`;
  }
  bindTabChromeEvents();
  bindTabContentEvents(activeTab);
}

function renderPalette() {
  elements.paletteOverlay.classList.toggle("hidden", !state.paletteOpen);
  if (!state.paletteOpen) return;
  elements.paletteResults.innerHTML = paletteActions.map((action) => `
    <button class="palette-item" data-palette-action="${escapeHtml(action.id)}" type="button">
      <strong>${escapeHtml(action.label)}</strong>
      <span>${escapeHtml(action.description)}</span>
    </button>
  `).join("");
  elements.paletteResults.querySelectorAll("[data-palette-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = paletteActions.find((entry) => entry.id === button.dataset.paletteAction);
      if (!action) return;
      action.run();
      state.paletteOpen = false;
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
  elements.workflowRunsMeta.textContent = runs.length
    ? `${Math.min(CONFIG.maxWorklistRuns, runs.length)} of ${runs.length} indexed runs · ${selectedCount} selected`
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
    </article>
  `).join("");
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
        <div class="run-row-actions">
          <label class="select-run">
            <input type="checkbox" data-select-run="${escapeHtml(run.run_id)}" ${selected ? "checked" : ""} ${disableSelection ? "disabled" : ""}>
            <span>Select</span>
          </label>
          <button class="ghost-btn" type="button" data-open-run="${escapeHtml(run.run_id)}">Open run</button>
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
  if (tab.kind === "compare") {
    elements.tabContent.querySelectorAll("[data-open-run]").forEach((button) => {
      button.addEventListener("click", () => openRunDetailTab(button.dataset.openRun));
    });
    elements.tabContent.querySelectorAll("[data-open-artifacts]").forEach((button) => {
      button.addEventListener("click", () => openArtifactsTabForRun(button.dataset.openArtifacts));
    });
  }
  if (tab.kind === "artifacts") {
    elements.tabContent.querySelectorAll("[data-open-external]").forEach((button) => {
      button.addEventListener("click", () => {
        const url = absoluteUrl(button.dataset.openExternal);
        if (url) window.quantlabDesktop.openExternal(url);
      });
    });
    elements.tabContent.querySelectorAll("[data-open-run]").forEach((button) => {
      button.addEventListener("click", () => openRunDetailTab(button.dataset.openRun));
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
  if (normalized.includes("open ops") || normalized.includes("paper ops")) {
    openResearchTab("ops", "Paper Ops", "#/ops");
    pushMessage("assistant", "Opened the Paper Ops surface.");
    return;
  }
  if (normalized.includes("open runs") || normalized === "runs") {
    openResearchTab("runs", "Runs", "#/");
    pushMessage("assistant", "Opened the run explorer.");
    return;
  }
  if (normalized.includes("latest run")) {
    openLatestRunTab();
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
  pushMessage("assistant", "This shell now supports real backend-backed actions. Try:\n- launch run ticker ETH-USD start 2023-01-01 end 2024-01-01\n- launch sweep config configs/sweeps/example.yaml\n- open latest run\n- compare selected\n- show artifacts\n- show runtime status");
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

function openRunDetailTab(runId) {
  const run = findRun(runId);
  if (!run) {
    pushMessage("assistant", `Run ${runId} is not present in the current registry snapshot.`);
    return;
  }
  openResearchTab("runs", `Run ${run.run_id}`, `#/run/${encodeURIComponent(run.run_id)}`);
}

function openCompareSelectionTab() {
  const selectedRuns = getSelectedRuns();
  if (selectedRuns.length < 2) {
    pushMessage("assistant", "Select 2 to 4 runs in the worklist before opening compare.");
    return;
  }
  upsertTab({
    id: `compare:${selectedRuns.map((run) => run.run_id).join("|")}`,
    kind: "compare",
    navKind: "compare",
    title: `Compare ${selectedRuns.length} runs`,
    runIds: selectedRuns.map((run) => run.run_id),
  });
  pushMessage("assistant", `Opened a compare tab for ${selectedRuns.length} selected runs.`);
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

function closeTab(tabId) {
  state.tabs = state.tabs.filter((tab) => tab.id !== tabId);
  if (state.activeTabId === tabId) state.activeTabId = state.tabs[0]?.id || null;
  renderTabs();
}

function syncNav(kind) {
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("is-active"));
  const mapping = { chat: "open-chat", launch: "open-launch", runs: "open-runs", compare: "open-compare", ops: "open-ops" };
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
  const ticker = extractNamedValue(prompt, "ticker");
  const start = extractNamedValue(prompt, "start");
  const end = extractNamedValue(prompt, "end");
  if (!ticker || !start || !end) return null;
  const params = { ticker, start, end };
  const interval = extractNamedValue(prompt, "interval");
  const cash = extractNamedValue(prompt, "cash");
  if (interval) params.interval = interval;
  if (cash) params.initial_cash = cash;
  if (/\bpaper\b/i.test(prompt)) params.paper = true;
  return { command: "run", params };
}

function parseLaunchSweepPrompt(prompt) {
  if (!prompt.trim().toLowerCase().startsWith("launch sweep")) return null;
  const configPath = extractNamedValue(prompt, "config");
  if (!configPath) return null;
  const payload = { command: "sweep", params: { config_path: configPath } };
  const outDir = extractNamedValue(prompt, "out");
  if (outDir) payload.params.out_dir = outDir;
  return payload;
}

function extractNamedValue(prompt, key) {
  const match = String(prompt).match(new RegExp(`${key}\\s+([^\\s]+)`, "i"));
  return match ? match[1].trim() : "";
}

function extractRunIdAfterPrefix(prompt, prefix) {
  const normalizedPrefix = prefix.trim().toLowerCase();
  const normalized = prompt.trim().toLowerCase();
  if (!normalized.startsWith(normalizedPrefix)) return "";
  return prompt.trim().slice(prefix.length).trim();
}

function renderCompareTab(tab) {
  const runs = (tab.runIds || []).map(findRun).filter(Boolean);
  if (runs.length < 2) {
    return `<div class="tab-placeholder">The selected compare set is no longer available in the registry.</div>`;
  }
  const bestSharpe = runs.reduce((best, run) => (metricValue(run.sharpe_simple) > metricValue(best?.sharpe_simple) ? run : best), runs[0]);
  const bestReturn = runs.reduce((best, run) => (metricValue(run.total_return) > metricValue(best?.total_return) ? run : best), runs[0]);
  const bestDrawdown = runs.reduce((best, run) => (metricValue(run.max_drawdown) > metricValue(best?.max_drawdown) ? run : best), runs[0]);
  return `
    <div class="compare-shell">
      <div class="tab-summary-grid">
        ${renderSummaryCard("Compared runs", String(runs.length))}
        ${renderSummaryCard("Best sharpe", `${bestSharpe.run_id} · ${formatNumber(bestSharpe.sharpe_simple)}`)}
        ${renderSummaryCard("Best return", `${bestReturn.run_id} · ${formatPercent(bestReturn.total_return)}`, toneClass(bestReturn.total_return, true))}
        ${renderSummaryCard("Best drawdown", `${bestDrawdown.run_id} · ${formatPercent(bestDrawdown.max_drawdown)}`, toneClass(bestDrawdown.max_drawdown, false))}
      </div>
      <div class="compare-grid">
        ${runs.map((run) => `
          <article class="compare-card">
            <div class="artifact-top">
              <div>
                <div class="section-label">${escapeHtml(titleCase(run.mode || "unknown"))}</div>
                <h3>${escapeHtml(run.run_id)}</h3>
              </div>
              <div class="workflow-actions">
                <button class="ghost-btn" type="button" data-open-run="${escapeHtml(run.run_id)}">Open run</button>
                <button class="ghost-btn" type="button" data-open-artifacts="${escapeHtml(run.run_id)}">Artifacts</button>
              </div>
            </div>
            <div class="compare-meta">${escapeHtml(run.ticker || "-")} · ${escapeHtml(formatDateTime(run.created_at))}</div>
            <dl class="metric-list">
              ${compareMetric("Return", formatPercent(run.total_return), toneClass(run.total_return, true))}
              ${compareMetric("Sharpe", formatNumber(run.sharpe_simple), "")}
              ${compareMetric("Drawdown", formatPercent(run.max_drawdown), toneClass(run.max_drawdown, false))}
              ${compareMetric("Trades", formatCount(run.trades), "")}
              ${compareMetric("Window", `${run.start || "-"} -> ${run.end || "-"}`, "")}
              ${compareMetric("Commit", shortCommit(run.git_commit) || "-", "")}
            </dl>
          </article>
        `).join("")}
      </div>
    </div>
  `;
}

function renderArtifactsTab(tab) {
  const run = findRun(tab.runId);
  if (!run) return `<div class="tab-placeholder">The requested run is no longer present in the registry.</div>`;
  if (tab.status === "loading") return `<div class="tab-placeholder">Reading canonical artifacts for ${escapeHtml(run.run_id)}...</div>`;
  if (tab.status === "error") return `<div class="tab-placeholder">${escapeHtml(tab.error || "Could not load artifact metadata.")}</div>`;
  const detail = tab.detail || { report: null, reportUrl: null };
  const report = detail.report;
  const artifacts = Array.isArray(report?.artifacts) ? report.artifacts : [];
  return `
    <div class="artifact-shell">
      <div class="artifact-top">
        <div>
          <div class="section-label">Artifacts</div>
          <h3>${escapeHtml(run.run_id)}</h3>
          <div class="artifact-meta">${escapeHtml(run.ticker || "-")} · ${escapeHtml(formatDateTime(run.created_at))}</div>
        </div>
        <div class="workflow-actions">
          <button class="ghost-btn" type="button" data-open-run="${escapeHtml(run.run_id)}">Open run</button>
          ${detail.reportUrl ? `<button class="ghost-btn" type="button" data-open-external="${escapeHtml(detail.reportUrl)}">Raw report</button>` : ""}
        </div>
      </div>
      <div class="artifact-grid">
        <section class="artifact-panel">
          <div class="section-label">Run metadata</div>
          <h3>Window and output path</h3>
          <div class="artifact-meta">${escapeHtml(`${run.start || "-"} -> ${run.end || "-"}`)}</div>
          <div class="artifact-path">${escapeHtml(run.path || "-")}</div>
        </section>
        <section class="artifact-panel">
          <div class="section-label">Artifact manifest</div>
          <h3>Files</h3>
          ${artifacts.length ? `<div class="artifact-list">
            ${artifacts.map((artifact) => {
              const href = buildRunArtifactHref(run.path, artifact.file_name);
              return `<button class="artifact-link" type="button" data-open-external="${escapeHtml(href)}"><span>${escapeHtml(artifact.file_name)}</span><span>${escapeHtml(formatBytes(artifact.size_bytes))}</span></button>`;
            }).join("")}
          </div>` : `<div class="empty-state">The canonical report does not expose an artifact manifest for this run.</div>`}
        </section>
      </div>
    </div>
  `;
}

function renderSummaryCard(label, value, tone = "") {
  return `<article class="summary-card"><div class="label">${escapeHtml(label)}</div><div class="value ${escapeHtml(tone)}">${escapeHtml(value)}</div></article>`;
}

function compareMetric(label, value, extraClass) {
  return `<div class="${escapeHtml(extraClass)}"><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`;
}

function upsertTab(nextTab) {
  const index = state.tabs.findIndex((tab) => tab.id === nextTab.id);
  if (index >= 0) state.tabs[index] = { ...state.tabs[index], ...nextTab };
  else state.tabs.push(nextTab);
  state.activeTabId = nextTab.id;
  renderTabs();
}

function rerenderContextualTabs() {
  if (state.tabs.some((tab) => tab.kind === "compare" || tab.kind === "artifacts")) renderTabs();
}

async function loadRunDetail(runId) {
  if (state.detailCache.has(runId)) return state.detailCache.get(runId);
  const run = findRun(runId);
  if (!run?.path) throw new Error(`Run ${runId} has no accessible artifact path.`);
  let detail = { report: null, reportUrl: null };
  for (const artifact of CONFIG.detailArtifacts) {
    const href = buildRunArtifactHref(run.path, artifact);
    try {
      const report = await window.quantlabDesktop.requestJson(href);
      detail = { report, reportUrl: href };
      break;
    } catch (_error) {
      // Keep trying the remaining artifact names.
    }
  }
  state.detailCache.set(runId, detail);
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
  return `${state.workspace.serverUrl}/research_ui/index.html#/`;
}

function getRuns() {
  return Array.isArray(state.snapshot?.runsRegistry?.runs) ? state.snapshot.runsRegistry.runs : [];
}

function getLatestRun() {
  return getRuns()[0] || null;
}

function getSelectedRuns() {
  return state.selectedRunIds.map(findRun).filter(Boolean);
}

function findRun(runId) {
  return getRuns().find((run) => run.run_id === runId) || null;
}

function summarizeLaunchPayload(payload) {
  return payload.command === "run"
    ? `Run ${payload.params.ticker} ${payload.params.start} -> ${payload.params.end}`
    : `Sweep ${payload.params.config_path}`;
}

function buildRunArtifactHref(runPath, fileName) {
  const base = toOutputsHref(runPath);
  return base ? `${base}/${fileName}` : "";
}

function toOutputsHref(absolutePath) {
  const match = String(absolutePath || "").match(/[\\/](outputs[\\/].*)$/i);
  return match ? `/${match[1].replace(/\\/g, "/")}` : "";
}

function absoluteUrl(relativeOrUrl) {
  if (!relativeOrUrl) return "";
  if (/^https?:\/\//i.test(relativeOrUrl)) return relativeOrUrl;
  return state.workspace.serverUrl ? `${state.workspace.serverUrl.replace(/\/$/, "")}${relativeOrUrl}` : "";
}

function runtimeChip(label, value, tone) {
  return `<div class="runtime-chip ${escapeHtml(tone)}"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(value)}</span></div>`;
}

function titleCase(value) {
  return String(value || "").replace(/[_-]+/g, " ").replace(/\b\w/g, (match) => match.toUpperCase());
}

function shortCommit(value) {
  return value ? String(value).slice(0, 7) : "";
}

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat(undefined, { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(date);
}

function formatPercent(value) {
  return typeof value === "number" && !Number.isNaN(value) ? `${(value * 100).toFixed(2)}%` : "-";
}

function formatNumber(value) {
  return typeof value === "number" && !Number.isNaN(value) ? value.toFixed(2) : "-";
}

function formatCount(value) {
  return typeof value === "number" && !Number.isNaN(value) ? value.toFixed(0) : "-";
}

function formatBytes(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "-";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function toneClass(value, higherIsBetter) {
  if (typeof value !== "number" || Number.isNaN(value)) return "";
  const good = higherIsBetter ? value > 0 : value > -0.15;
  const bad = higherIsBetter ? value < 0 : value < -0.3;
  if (good) return "tone-positive";
  if (bad) return "tone-negative";
  return "";
}

function metricValue(value) {
  return typeof value === "number" && !Number.isNaN(value) ? value : Number.NEGATIVE_INFINITY;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
