import * as decisionStore from "./modules/decision-store.js";
import * as sweepDecisionStore from "./modules/sweep-decision-store.js";
import {
  absoluteUrl as buildAbsoluteUrl,
  basenamePath as basenameValue,
  buildRunArtifactHref as buildArtifactHref,
  escapeHtml as escapeMarkup,
  escapeRegex as escapePattern,
  formatBytes as formatByteCount,
  formatCount as formatNumericCount,
  formatDateTime as formatDateTimeValue,
  formatLogPreview as formatLogText,
  formatNumber as formatNumericValue,
  formatPercent as formatPercentValue,
  parseCsvRows as parseCsvPreviewRows,
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
  renderCompareTab as renderCompareTabView,
  renderExperimentsTab as renderExperimentsTabView,
  renderJobTab as renderJobTabView,
  renderPaperOpsTab as renderPaperOpsTabView,
  renderRunTab as renderRunTabView,
  renderSweepDecisionTab as renderSweepDecisionTabView,
  renderSummaryCard as renderSummaryCardView,
} from "./modules/tab-renderers.js";

const CONFIG = {
  runsIndexPath: "/outputs/runs/runs_index.json",
  launchControlPath: "/api/launch-control",
  paperHealthPath: "/api/paper-sessions-health",
  brokerHealthPath: "/api/broker-submissions-health",
  stepbitWorkspacePath: "/api/stepbit-workspace",
  detailArtifacts: ["report.json", "run_report.json"],
  experimentsConfigDir: "configs/experiments",
  sweepsOutputDir: "outputs/sweeps",
  refreshIntervalMs: 15000,
  maxWorklistRuns: 8,
  maxRecentJobs: 4,
  maxLogPreviewChars: 5000,
  maxCandidateCompare: 4,
  maxExperimentsConfigs: 12,
  maxRecentSweeps: 8,
  maxSweepRows: 5,
  maxSweepDecisionCompare: 4,
  persistDebounceMs: 400,
};

const state = {
  workspace: { status: "starting", serverUrl: null, logs: [], error: null },
  snapshot: null,
  candidatesStore: defaultCandidatesStore(),
  candidatesLoaded: false,
  sweepDecisionStore: defaultSweepDecisionStore(),
  sweepDecisionLoaded: false,
  selectedRunIds: [],
  detailCache: new Map(),
  experimentsWorkspace: { status: "idle", configs: [], sweeps: [], error: null, updatedAt: null },
  experimentConfigPreviewCache: new Map(),
  isSubmittingLaunch: false,
  launchFeedback: "Use deterministic inputs or ask from chat.",
  refreshTimer: null,
  isStepbitSubmitting: false,
  snapshotStatus: { status: "idle", error: null, lastSuccessAt: null },
  isRetryingWorkspace: false,
  chatMessages: [
    {
      role: "assistant",
      label: "quantlab",
      content:
        "QuantLab Desktop now supports a real workflow.\n\nTry:\n- open experiments\n- open sweep handoff\n- launch run ticker ETH-USD start 2023-01-01 end 2024-01-01\n- launch sweep config configs/experiments/eth_2023_grid.yaml\n- open latest run\n- compare selected\n- show artifacts\n- open latest failed launch\n- explain latest failure\n- ask stepbit explain the latest failed launch",
    },
  ],
  tabs: [],
  activeTabId: null,
  paletteOpen: false,
  paletteQuery: "",
  workspaceStoreLoaded: false,
  workspacePersistTimer: null,
};

const elements = {
  runtimeSummary: document.getElementById("runtime-summary"),
  runtimeMeta: document.getElementById("runtime-meta"),
  runtimeAlert: document.getElementById("runtime-alert"),
  runtimeRetry: document.getElementById("runtime-retry"),
  runtimeChips: document.getElementById("runtime-chips"),
  chatLog: document.getElementById("chat-log"),
  chatForm: document.getElementById("chat-form"),
  chatInput: document.getElementById("chat-input"),
  chatStepbit: document.getElementById("chat-stepbit"),
  chatAdapterStatus: document.getElementById("chat-adapter-status"),
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
  ["experiments", "Open Experiments", "Open the native experiments and sweeps workspace.", () => openExperimentsTab()],
  ["sweep-handoff", "Open Sweep Handoff", "Open the local sweep decision handoff compare.", () => openSweepDecisionTab()],
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
  ["stepbit-failure", "Ask Stepbit About Failure", "Use the Stepbit-backed adapter to inspect the latest failed launch.", () => askStepbitAboutLatestFailure()],
  ["artifacts", "Show Artifacts", "Open artifacts for the selected or latest run.", () => openArtifactsForPreferredRun()],
  ["runtime", "Show Runtime Status", "Summarize runtime health in chat.", () => summarizeRuntimeInChat()],
].map(([id, label, description, run]) => ({ id, label, description, run }));

document.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  try {
    restoreShellWorkspaceStore(await window.quantlabDesktop.getShellWorkspaceStore());
  } catch (_error) {
    // Workspace restore is optional; the shell can still boot from a cold state.
  } finally {
    state.workspaceStoreLoaded = true;
  }
  renderAll();
  try {
    state.candidatesStore = normalizeCandidatesStore(await window.quantlabDesktop.getCandidatesStore());
  } catch (_error) {
    state.candidatesStore = defaultCandidatesStore();
  } finally {
    state.candidatesLoaded = true;
  }
  try {
    state.sweepDecisionStore = normalizeSweepDecisionStore(await window.quantlabDesktop.getSweepDecisionStore());
  } catch (_error) {
    state.sweepDecisionStore = defaultSweepDecisionStore();
  } finally {
    state.sweepDecisionLoaded = true;
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
  if (state.workspacePersistTimer) window.clearTimeout(state.workspacePersistTimer);
  if (state.workspaceStoreLoaded) {
    window.quantlabDesktop.saveShellWorkspaceStore(serializeShellWorkspaceStore()).catch(() => {});
  }
});

function bindEvents() {
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.action;
      if (action === "open-chat") focusChat();
      if (action === "open-experiments") openExperimentsTab();
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
  elements.chatStepbit.addEventListener("click", () => {
    const prompt = elements.chatInput.value.trim();
    if (!prompt) return;
    handleStepbitPrompt(prompt);
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
  elements.workflowLaunchCommand.addEventListener("change", () => {
    renderWorkflow();
    scheduleShellWorkspacePersist();
  });
  [
    elements.workflowLaunchTicker,
    elements.workflowLaunchStart,
    elements.workflowLaunchEnd,
    elements.workflowLaunchInterval,
    elements.workflowLaunchCash,
    elements.workflowLaunchConfigPath,
    elements.workflowLaunchOutDir,
  ].forEach((input) => {
    input.addEventListener("input", () => scheduleShellWorkspacePersist());
  });
  elements.workflowLaunchPaper.addEventListener("change", () => scheduleShellWorkspacePersist());
  elements.runtimeRetry.addEventListener("click", () => retryWorkspaceRuntime());
  elements.workflowOpenCompare.addEventListener("click", () => openCompareSelectionTab());
  elements.workflowClearSelection.addEventListener("click", () => {
    state.selectedRunIds = [];
    renderWorkflow();
    scheduleShellWorkspacePersist();
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
    state.snapshotStatus = { status: "ok", error: null, lastSuccessAt: new Date().toISOString() };
    const validIds = new Set(getRuns().map((run) => run.run_id));
    const filteredSelection = state.selectedRunIds.filter((runId) => validIds.has(runId));
    if (filteredSelection.length !== state.selectedRunIds.length) {
      state.selectedRunIds = filteredSelection;
      scheduleShellWorkspacePersist();
    }
    renderWorkspaceState();
    renderWorkflow();
    refreshLiveJobTabs();
    rerenderContextualTabs();
    if (state.tabs.some((tab) => ["experiments", "sweep-decision"].includes(tab.kind))) {
      refreshExperimentsWorkspace({ focusTab: false, silent: true });
    }
  } catch (error) {
    state.snapshotStatus = {
      status: "error",
      error: error?.message || "The local API is unavailable.",
      lastSuccessAt: state.snapshotStatus.lastSuccessAt,
    };
    renderWorkspaceState();
    // Keep the shell usable even if optional surfaces are down.
  }
}

function renderAll() {
  renderChat();
  renderTabs();
  renderPalette();
  renderWorkflow();
  renderChatAdapterStatus();
}

function defaultShellWorkspaceStore() {
  return {
    version: 1,
    active_tab_id: null,
    selected_run_ids: [],
    tabs: [],
    launch_form: {
      command: "run",
      ticker: "",
      start: "",
      end: "",
      interval: "",
      cash: "",
      paper: false,
      config_path: "",
      out_dir: "",
    },
  };
}

function normalizeShellWorkspaceStore(store) {
  const fallback = defaultShellWorkspaceStore();
  if (!store || typeof store !== "object") return fallback;
  const tabs = Array.isArray(store.tabs) ? store.tabs.map(normalizeShellTab).filter(Boolean) : [];
  const activeTabId = typeof store.active_tab_id === "string" ? store.active_tab_id : null;
  return {
    version: 1,
    active_tab_id: tabs.some((tab) => tab.id === activeTabId) ? activeTabId : tabs[0]?.id || null,
    selected_run_ids: Array.isArray(store.selected_run_ids)
      ? store.selected_run_ids.filter((value) => typeof value === "string" && value).slice(0, 4)
      : [],
    tabs,
    launch_form: normalizeLaunchFormState(store.launch_form),
  };
}

function normalizeShellTab(tab) {
  if (!tab || typeof tab !== "object" || typeof tab.id !== "string" || typeof tab.kind !== "string") return null;
  const base = {
    id: String(tab.id),
    kind: String(tab.kind),
    navKind: typeof tab.navKind === "string" ? tab.navKind : "",
    title: typeof tab.title === "string" ? tab.title : "",
  };
  if (base.kind === "iframe") {
    if (typeof tab.url !== "string" || !tab.url) return null;
    return { ...base, url: tab.url };
  }
  if (base.kind === "run" || base.kind === "artifacts") {
    if (typeof tab.runId !== "string" || !tab.runId) return null;
    return { ...base, runId: tab.runId };
  }
  if (base.kind === "compare") {
    const runIds = Array.isArray(tab.runIds) ? uniqueRunIds(tab.runIds.filter((value) => typeof value === "string" && value)).slice(0, CONFIG.maxCandidateCompare) : [];
    if (!runIds.length) return null;
    return { ...base, runIds, rankMetric: typeof tab.rankMetric === "string" ? tab.rankMetric : "" };
  }
  if (base.kind === "candidates") {
    return { ...base, filter: typeof tab.filter === "string" ? tab.filter : "all" };
  }
  if (base.kind === "experiments") {
    return {
      ...base,
      selectedConfigPath: typeof tab.selectedConfigPath === "string" ? tab.selectedConfigPath : "",
      selectedSweepId: typeof tab.selectedSweepId === "string" ? tab.selectedSweepId : "",
    };
  }
  if (base.kind === "sweep-decision") {
    return { ...base, rankMetric: typeof tab.rankMetric === "string" ? tab.rankMetric : "" };
  }
  if (base.kind === "job") {
    if (typeof tab.requestId !== "string" || !tab.requestId) return null;
    return { ...base, requestId: tab.requestId };
  }
  if (base.kind === "paper") return base;
  return null;
}

function normalizeLaunchFormState(formState) {
  const fallback = defaultShellWorkspaceStore().launch_form;
  if (!formState || typeof formState !== "object") return fallback;
  return {
    command: formState.command === "sweep" ? "sweep" : "run",
    ticker: typeof formState.ticker === "string" ? formState.ticker : "",
    start: typeof formState.start === "string" ? formState.start : "",
    end: typeof formState.end === "string" ? formState.end : "",
    interval: typeof formState.interval === "string" ? formState.interval : "",
    cash: typeof formState.cash === "string" ? formState.cash : "",
    paper: Boolean(formState.paper),
    config_path: typeof formState.config_path === "string" ? formState.config_path : "",
    out_dir: typeof formState.out_dir === "string" ? formState.out_dir : "",
  };
}

function collectLaunchFormState() {
  return normalizeLaunchFormState({
    command: elements.workflowLaunchCommand.value || "run",
    ticker: elements.workflowLaunchTicker.value,
    start: elements.workflowLaunchStart.value,
    end: elements.workflowLaunchEnd.value,
    interval: elements.workflowLaunchInterval.value,
    cash: elements.workflowLaunchCash.value,
    paper: elements.workflowLaunchPaper.checked,
    config_path: elements.workflowLaunchConfigPath.value,
    out_dir: elements.workflowLaunchOutDir.value,
  });
}

function applyLaunchFormState(formState) {
  const normalized = normalizeLaunchFormState(formState);
  elements.workflowLaunchCommand.value = normalized.command;
  elements.workflowLaunchTicker.value = normalized.ticker;
  elements.workflowLaunchStart.value = normalized.start;
  elements.workflowLaunchEnd.value = normalized.end;
  elements.workflowLaunchInterval.value = normalized.interval;
  elements.workflowLaunchCash.value = normalized.cash;
  elements.workflowLaunchPaper.checked = normalized.paper;
  elements.workflowLaunchConfigPath.value = normalized.config_path;
  elements.workflowLaunchOutDir.value = normalized.out_dir;
}

function serializeTabForWorkspace(tab) {
  return normalizeShellTab(tab);
}

function serializeShellWorkspaceStore() {
  return normalizeShellWorkspaceStore({
    active_tab_id: state.activeTabId,
    selected_run_ids: state.selectedRunIds,
    tabs: state.tabs.map(serializeTabForWorkspace).filter(Boolean),
    launch_form: collectLaunchFormState(),
  });
}

function restoreShellWorkspaceStore(store) {
  const restored = normalizeShellWorkspaceStore(store);
  state.tabs = restored.tabs;
  state.activeTabId = restored.active_tab_id;
  state.selectedRunIds = restored.selected_run_ids;
  applyLaunchFormState(restored.launch_form);
}

function scheduleShellWorkspacePersist() {
  if (!state.workspaceStoreLoaded) return;
  if (state.workspacePersistTimer) window.clearTimeout(state.workspacePersistTimer);
  state.workspacePersistTimer = window.setTimeout(() => {
    state.workspacePersistTimer = null;
    window.quantlabDesktop.saveShellWorkspaceStore(serializeShellWorkspaceStore()).catch(() => {});
  }, CONFIG.persistDebounceMs);
}

function clearElement(element) {
  element.replaceChildren();
}

function appendChildren(element, ...children) {
  const fragment = document.createDocumentFragment();
  children.flat().filter(Boolean).forEach((child) => fragment.appendChild(child));
  element.replaceChildren(fragment);
}

function createElementNode(tagName, options = {}, children = []) {
  const {
    className = "",
    text = null,
    attrs = {},
    dataset = {},
    type = null,
    disabled = null,
    checked = null,
  } = options;
  const element = document.createElement(tagName);
  if (className) element.className = className;
  if (text !== null && text !== undefined) element.textContent = String(text);
  if (type) element.type = type;
  if (disabled !== null) element.disabled = Boolean(disabled);
  if (checked !== null) element.checked = Boolean(checked);
  Object.entries(attrs).forEach(([key, value]) => {
    if (value !== null && value !== undefined) element.setAttribute(key, String(value));
  });
  Object.entries(dataset).forEach(([key, value]) => {
    if (value !== null && value !== undefined) element.dataset[key] = String(value);
  });
  children.flat().filter(Boolean).forEach((child) => element.appendChild(child));
  return element;
}

function createTextDiv(className, text) {
  return createElementNode("div", { className, text });
}

function createEmptyStateNode(text) {
  return createElementNode("div", { className: "empty-state", text });
}

function renderMarkupInto(container, markup) {
  const range = document.createRange();
  range.selectNodeContents(container);
  const fragment = range.createContextualFragment(markup);
  container.replaceChildren(fragment);
}

function renderWorkspaceState() {
  const { status, serverUrl, error, source } = state.workspace;
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
    ? `${serverUrl}/research_ui/index.html${source === "external" ? " · external server" : ""}`
    : "Waiting for localhost server URL.";
  const runtimeAlert = buildRuntimeAlert();
  elements.runtimeAlert.textContent = runtimeAlert.message;
  elements.runtimeAlert.classList.toggle("hidden", !runtimeAlert.message);
  elements.runtimeAlert.classList.toggle("warn", runtimeAlert.tone === "warn");
  elements.runtimeAlert.classList.toggle("down", runtimeAlert.tone === "down");
  elements.runtimeRetry.textContent = runtimeAlert.actionLabel;
  elements.runtimeRetry.classList.toggle("hidden", !runtimeAlert.actionLabel);
  elements.runtimeRetry.disabled = state.isRetryingWorkspace;
  appendChildren(
    elements.runtimeChips,
    createRuntimeChipNode("QuantLab", status === "ready" ? "up" : status === "starting" ? "starting" : "down", status === "ready" ? "up" : status === "starting" ? "warn" : "down"),
    createRuntimeChipNode("Runs", `${runs.length} indexed`, runs.length ? "up" : "warn"),
    createRuntimeChipNode("Paper", String(paperCount), paperCount ? "up" : "warn"),
    createRuntimeChipNode("Broker", String(brokerCount), brokerCount ? "up" : "warn"),
    createRuntimeChipNode("API", state.snapshotStatus.status === "error" ? "degraded" : state.snapshotStatus.lastSuccessAt ? "ok" : "pending", state.snapshotStatus.status === "error" ? "down" : state.snapshotStatus.lastSuccessAt ? "up" : "warn"),
    createRuntimeChipNode("Stepbit app", stepbit.frontend_reachable ? "up" : "down", stepbit.frontend_reachable ? "up" : "down"),
    createRuntimeChipNode("Stepbit core", stepbit.core_ready ? "ready" : stepbit.core_reachable ? "up" : "down", stepbit.core_ready ? "up" : stepbit.core_reachable ? "warn" : "down"),
  );
  renderChatAdapterStatus();
}

function buildRuntimeAlert() {
  if (state.workspace.status === "error" || state.workspace.status === "stopped") {
    const recentLogs = (state.workspace.logs || []).slice(-4).join("\n");
    return {
      tone: "down",
      actionLabel: "Retry boot",
      message: `${state.workspace.status === "error" ? "Boot failed" : "Runtime stopped"}${state.workspace.error ? `: ${state.workspace.error}` : "."}${recentLogs ? `\n\nRecent log:\n${recentLogs}` : ""}`,
    };
  }
  if (state.snapshotStatus.status === "error") {
    return {
      tone: "warn",
      actionLabel: "Retry API",
      message: `API unavailable: ${state.snapshotStatus.error || "local request failed."}`,
    };
  }
  if (state.workspace.status === "starting") {
    return {
      tone: "warn",
      actionLabel: "",
      message: "QuantLab Desktop is waiting for the local research surface to become reachable.",
    };
  }
  return { tone: "", actionLabel: "", message: "" };
}

async function retryWorkspaceRuntime() {
  if (state.isRetryingWorkspace) return;
  state.isRetryingWorkspace = true;
  renderWorkspaceState();
  try {
    if (state.workspace.status === "error" || state.workspace.status === "stopped" || !state.workspace.serverUrl) {
      state.workspace = await window.quantlabDesktop.restartWorkspaceServer();
      renderWorkspaceState();
    }
    await refreshSnapshot();
  } finally {
    state.isRetryingWorkspace = false;
    renderWorkspaceState();
  }
}

function renderChat() {
  appendChildren(
    elements.chatLog,
    state.chatMessages.map((message) =>
      createElementNode("article", { className: `message ${message.role}` }, [
        createTextDiv("message-role", message.label || message.role),
        createTextDiv("message-body", message.content),
      ]),
    ),
  );
  elements.chatLog.scrollTop = elements.chatLog.scrollHeight;
}

function getStepbitChatAvailability() {
  const stepbit = state.snapshot?.stepbitWorkspace?.live_urls || {};
  return {
    frontendReachable: Boolean(stepbit.frontend_reachable),
    backendReachable: Boolean(stepbit.backend_reachable),
    coreReachable: Boolean(stepbit.core_reachable),
    coreReady: Boolean(stepbit.core_ready),
  };
}

function renderChatAdapterStatus() {
  const availability = getStepbitChatAvailability();
  const isReady = availability.backendReachable && availability.coreReachable;
  elements.chatStepbit.disabled = !isReady || state.isStepbitSubmitting;
  elements.chatAdapterStatus.textContent = state.isStepbitSubmitting
    ? "Stepbit adapter running..."
    : isReady
    ? availability.coreReady
      ? "Stepbit adapter ready."
      : "Stepbit adapter up, core warming."
    : availability.backendReachable
    ? "Stepbit backend up, core unavailable."
    : "Stepbit adapter offline.";
}

function renderTabs() {
  if (!state.tabs.length) {
    clearElement(elements.tabsBar);
    appendChildren(
      elements.tabContent,
      createElementNode(
        "div",
        {
          className: "tab-placeholder",
          text: "No context tab is open yet.\n\nUse chat, quick command, or the workflow panel to launch work, open runs, compare candidates, or inspect artifacts.",
        },
      ),
    );
    elements.topbarTitle.textContent = "Chat";
    syncNav("chat");
    return;
  }
  appendChildren(
    elements.tabsBar,
    state.tabs.map((tab) =>
      createElementNode(
        "button",
        {
          className: `tab-pill ${tab.id === state.activeTabId ? "is-active" : ""}`,
          dataset: { tabId: tab.id },
          type: "button",
        },
        [
          createElementNode("span", { text: tab.title }),
          createElementNode("span", { className: "tab-close", text: "×", dataset: { closeTab: tab.id } }),
        ],
      ),
    ),
  );
  const activeTab = state.tabs.find((tab) => tab.id === state.activeTabId) || state.tabs[0];
  state.activeTabId = activeTab.id;
  elements.topbarTitle.textContent = activeTab.title;
  syncNav(activeTab.navKind || activeTab.kind);
  if (activeTab.kind === "iframe") {
    appendChildren(
      elements.tabContent,
      createElementNode("iframe", {
        className: "tab-frame",
        attrs: { src: activeTab.url, title: activeTab.title },
      }),
    );
  } else if (activeTab.kind === "experiments") {
    renderMarkupInto(elements.tabContent, renderExperimentsTab(activeTab));
  } else if (activeTab.kind === "sweep-decision") {
    renderMarkupInto(elements.tabContent, renderSweepDecisionTab(activeTab));
  } else if (activeTab.kind === "run") {
    renderMarkupInto(elements.tabContent, renderRunTab(activeTab));
  } else if (activeTab.kind === "compare") {
    renderMarkupInto(elements.tabContent, renderCompareTab(activeTab));
  } else if (activeTab.kind === "artifacts") {
    renderMarkupInto(elements.tabContent, renderArtifactsTab(activeTab));
  } else if (activeTab.kind === "candidates") {
    renderMarkupInto(elements.tabContent, renderCandidatesTab(activeTab));
  } else if (activeTab.kind === "paper") {
    renderMarkupInto(elements.tabContent, renderPaperOpsTab(activeTab));
  } else if (activeTab.kind === "job") {
    renderMarkupInto(elements.tabContent, renderJobTab(activeTab));
  } else {
    appendChildren(elements.tabContent, createElementNode("div", { className: "tab-placeholder", text: activeTab.content || "" }));
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
  if (!visibleActions.length) {
    appendChildren(elements.paletteResults, createEmptyStateNode("No matching action. Try shortlist, baseline, compare, or paper."));
  } else {
    appendChildren(
      elements.paletteResults,
      visibleActions.map((action) =>
        createElementNode(
          "button",
          { className: "palette-item", dataset: { paletteAction: action.id }, type: "button" },
          [
            createElementNode("strong", { text: action.label }),
            createElementNode("span", { text: action.description }),
          ],
        ),
      ),
    );
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

function createRuntimeChipNode(label, value, tone) {
  return createElementNode("div", { className: `runtime-chip ${tone || ""}` }, [
    createElementNode("strong", { text: label }),
    createElementNode("span", { text: value }),
  ]);
}

function createCandidateFlagsNode(runId) {
  const fragment = document.createDocumentFragment();
  const labels = [];
  if (isBaselineRun(runId)) labels.push(["Baseline", "baseline"]);
  if (isShortlistedRun(runId)) labels.push(["Shortlist", "shortlist"]);
  if (isCandidateRun(runId)) labels.push(["Candidate", "candidate"]);
  if (!labels.length) labels.push(["Untracked", "neutral"]);
  labels.forEach(([text, tone]) => {
    fragment.appendChild(createElementNode("span", { className: `candidate-flag ${tone}`, text }));
  });
  return fragment;
}

function createMetricChipNode(label, value, extraTone = "") {
  return createElementNode("span", { className: `metric-chip${extraTone ? ` ${extraTone}` : ""}`, text: `${label} ${value}` });
}

function createJobCardNode(job) {
  const actions = createElementNode("div", { className: "workflow-actions" });
  actions.appendChild(createElementNode("button", { className: "ghost-btn", type: "button", text: "Review job", dataset: { openJob: job.request_id || "" } }));
  if (job.run_id) {
    actions.appendChild(createElementNode("button", { className: "ghost-btn", type: "button", text: "Open run", dataset: { openRun: job.run_id } }));
  }
  if (job.artifacts_href) {
    actions.appendChild(createElementNode("button", { className: "ghost-btn", type: "button", text: "Artifacts", dataset: { openJobArtifacts: job.request_id || "" } }));
  }
  return createElementNode("article", { className: "job-card" }, [
    createElementNode("div", { className: "job-top" }, [
      createElementNode("div", { className: "job-name" }, [
        createElementNode("strong", { text: titleCase(job.command || "unknown") }),
        createElementNode("span", { className: "job-meta", text: job.request_id || "-" }),
      ]),
      createElementNode("span", { className: `job-status ${job.status || "unknown"}`, text: titleCase(job.status || "unknown") }),
    ]),
    createElementNode("div", { text: job.summary || "-" }),
    createElementNode("div", { className: "job-meta", text: `${formatDateTime(job.started_at)}${job.ended_at ? ` · ended ${formatDateTime(job.ended_at)}` : " · running"}` }),
    actions,
  ]);
}

function createRunWorklistNode(run) {
  const selected = state.selectedRunIds.includes(run.run_id);
  const disableSelection = !selected && state.selectedRunIds.length >= 4;
  const selectLabel = createElementNode("label", { className: "select-run" }, [
    createElementNode("input", {
      type: "checkbox",
      dataset: { selectRun: run.run_id },
      checked: selected,
      disabled: disableSelection,
    }),
    createElementNode("span", { text: "Select" }),
  ]);
  const flags = createElementNode("div", { className: "run-row-flags" });
  flags.appendChild(createCandidateFlagsNode(run.run_id));
  return createElementNode("article", { className: "run-row" }, [
    createElementNode("div", { className: "run-row-top" }, [
      createElementNode("div", { className: "run-row-title" }, [
        createElementNode("strong", { text: run.run_id }),
        createElementNode("div", { className: "run-row-meta" }, [
          createElementNode("span", { text: titleCase(run.mode || "unknown") }),
          createElementNode("span", { text: run.ticker || "-" }),
          createElementNode("span", { text: formatDateTime(run.created_at) }),
        ]),
      ]),
      createElementNode("span", { className: "mode-chip", text: shortCommit(run.git_commit) || "no commit" }),
    ]),
    createElementNode("div", { className: "run-row-metrics" }, [
      createMetricChipNode("Return", formatPercent(run.total_return), toneClass(run.total_return, true)),
      createMetricChipNode("Sharpe", formatNumber(run.sharpe_simple)),
      createMetricChipNode("Drawdown", formatPercent(run.max_drawdown), toneClass(run.max_drawdown, false)),
      createMetricChipNode("Trades", formatCount(run.trades)),
    ]),
    flags,
    createElementNode("div", { className: "run-row-actions" }, [
      selectLabel,
      createElementNode("button", { className: "ghost-btn", type: "button", text: "Open run", dataset: { openRun: run.run_id } }),
      createElementNode("button", { className: "ghost-btn", type: "button", text: isCandidateRun(run.run_id) ? "Unmark candidate" : "Mark candidate", dataset: { toggleCandidate: run.run_id } }),
      createElementNode("button", { className: "ghost-btn", type: "button", text: "Artifacts", dataset: { openArtifacts: run.run_id } }),
    ]),
  ]);
}

function renderJobList(jobs) {
  if (!jobs.length) {
    appendChildren(elements.workflowJobsList, createEmptyStateNode("Launches from the shell or browser surface will appear here."));
    return;
  }
  appendChildren(elements.workflowJobsList, jobs.slice(0, CONFIG.maxRecentJobs).map((job) => createJobCardNode(job)));
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
    appendChildren(elements.workflowRunsList, createEmptyStateNode("The run index is still empty. Launch a run or wait for artifacts to appear."));
    return;
  }
  appendChildren(elements.workflowRunsList, runs.map((run) => createRunWorklistNode(run)));
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
      scheduleShellWorkspacePersist();
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
  if (tab.kind === "experiments") {
    elements.tabContent.querySelectorAll("[data-experiments-refresh]").forEach((button) => {
      button.addEventListener("click", () => refreshExperimentsWorkspace({ focusTab: true, silent: false }));
    });
    elements.tabContent.querySelectorAll("[data-experiment-config]").forEach((button) => {
      button.addEventListener("click", () => upsertTab({ id: tab.id, selectedConfigPath: button.dataset.experimentConfig }));
    });
    elements.tabContent.querySelectorAll("[data-experiment-launch-config]").forEach((button) => {
      button.addEventListener("click", async () => {
        const configPath = button.dataset.experimentLaunchConfig;
        if (!configPath) return;
        await submitLaunchRequest({ command: "sweep", params: { config_path: configPath } }, "experiments");
        await refreshExperimentsWorkspace({ focusTab: true, silent: true });
        upsertTab({ id: tab.id, selectedConfigPath: configPath });
      });
    });
    elements.tabContent.querySelectorAll("[data-experiment-open-path]").forEach((button) => {
      button.addEventListener("click", () => {
        if (button.dataset.experimentOpenPath) window.quantlabDesktop.openPath(button.dataset.experimentOpenPath);
      });
    });
    elements.tabContent.querySelectorAll("[data-experiment-open-file]").forEach((button) => {
      button.addEventListener("click", () => {
        if (button.dataset.experimentOpenFile) window.quantlabDesktop.openPath(button.dataset.experimentOpenFile);
      });
    });
    elements.tabContent.querySelectorAll("[data-open-path]").forEach((button) => {
      button.addEventListener("click", () => {
        if (button.dataset.openPath) window.quantlabDesktop.openPath(button.dataset.openPath);
      });
    });
    elements.tabContent.querySelectorAll("[data-experiment-sweep]").forEach((button) => {
      button.addEventListener("click", () => upsertTab({ id: tab.id, selectedSweepId: button.dataset.experimentSweep }));
    });
    elements.tabContent.querySelectorAll("[data-experiment-relaunch]").forEach((button) => {
      button.addEventListener("click", async () => {
        const configPath = button.dataset.experimentRelaunch;
        if (!configPath) return;
        await submitLaunchRequest({ command: "sweep", params: { config_path: configPath } }, "experiments");
        await refreshExperimentsWorkspace({ focusTab: true, silent: true });
      });
    });
    elements.tabContent.querySelectorAll("[data-sweep-track-entry]").forEach((button) => {
      button.addEventListener("click", () => {
        const row = findSweepDecisionRow(button.dataset.sweepTrackEntry);
        if (row) toggleSweepDecisionEntry(row);
      });
    });
    elements.tabContent.querySelectorAll("[data-sweep-shortlist-entry]").forEach((button) => {
      button.addEventListener("click", () => toggleSweepDecisionShortlist(button.dataset.sweepShortlistEntry));
    });
    elements.tabContent.querySelectorAll("[data-sweep-baseline-entry]").forEach((button) => {
      button.addEventListener("click", () => setSweepDecisionBaseline(button.dataset.sweepBaselineEntry));
    });
    elements.tabContent.querySelectorAll("[data-sweep-note-entry]").forEach((button) => {
      button.addEventListener("click", () => editSweepDecisionNote(button.dataset.sweepNoteEntry));
    });
    elements.tabContent.querySelectorAll("[data-open-sweep-handoff]").forEach((button) => {
      button.addEventListener("click", () => openSweepDecisionTab(button.dataset.openSweepHandoff || "tracked"));
    });
  }
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
    elements.tabContent.querySelectorAll("[data-open-artifacts]").forEach((button) => {
      button.addEventListener("click", () => openArtifactsTabForRun(button.dataset.openArtifacts));
    });
    elements.tabContent.querySelectorAll("[data-open-shortlist-compare]").forEach((button) => {
      button.addEventListener("click", () => openShortlistCompareTab());
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
  if (tab.kind === "sweep-decision") {
    elements.tabContent.querySelectorAll("[data-sweep-rank]").forEach((button) => {
      button.addEventListener("click", () => upsertTab({ id: tab.id, rankMetric: button.dataset.sweepRank }));
    });
    elements.tabContent.querySelectorAll("[data-sweep-track-entry]").forEach((button) => {
      button.addEventListener("click", () => {
        const row = findSweepDecisionRow(button.dataset.sweepTrackEntry) || getSweepDecisionResolvedEntry(button.dataset.sweepTrackEntry)?.row;
        if (row) toggleSweepDecisionEntry(row);
      });
    });
    elements.tabContent.querySelectorAll("[data-sweep-shortlist-entry]").forEach((button) => {
      button.addEventListener("click", () => toggleSweepDecisionShortlist(button.dataset.sweepShortlistEntry));
    });
    elements.tabContent.querySelectorAll("[data-sweep-baseline-entry]").forEach((button) => {
      button.addEventListener("click", () => setSweepDecisionBaseline(button.dataset.sweepBaselineEntry));
    });
    elements.tabContent.querySelectorAll("[data-sweep-note-entry]").forEach((button) => {
      button.addEventListener("click", () => editSweepDecisionNote(button.dataset.sweepNoteEntry));
    });
    elements.tabContent.querySelectorAll("[data-experiment-open-path]").forEach((button) => {
      button.addEventListener("click", () => {
        if (button.dataset.experimentOpenPath) window.quantlabDesktop.openPath(button.dataset.experimentOpenPath);
      });
    });
    elements.tabContent.querySelectorAll("[data-experiment-launch-config]").forEach((button) => {
      button.addEventListener("click", async () => {
        const configPath = button.dataset.experimentLaunchConfig;
        if (!configPath) return;
        await submitLaunchRequest({ command: "sweep", params: { config_path: configPath } }, "sweep-handoff");
        await refreshExperimentsWorkspace({ focusTab: false, silent: true });
      });
    });
  }
}

function extractStepbitPrompt(prompt) {
  const trimmed = String(prompt || "").trim();
  const prefixes = ["ask stepbit", "use stepbit", "stepbit:"];
  for (const prefix of prefixes) {
    if (trimmed.toLowerCase().startsWith(prefix)) {
      return prefix.endsWith(":") ? trimmed.slice(prefix.length).trim() : trimmed.slice(prefix.length).trim();
    }
  }
  return "";
}

function buildStepbitContextLines() {
  const runs = getRuns();
  const latestRun = getLatestRun();
  const selectedRunIds = getSelectedRuns().map((run) => run.run_id);
  const latestFailedJob = getLatestFailedJob();
  return [
    `QuantLab server status: ${state.workspace.status}`,
    `Indexed runs: ${runs.length}`,
    `Selected runs: ${selectedRunIds.join(", ") || "none"}`,
    `Candidate count: ${getCandidateEntries().length}`,
    `Shortlisted runs: ${getShortlistRunIds().join(", ") || "none"}`,
    `Baseline run: ${state.candidatesStore.baseline_run_id || "none"}`,
    `Latest run: ${latestRun?.run_id || "none"}`,
    `Latest failed launch: ${latestFailedJob?.request_id || "none"}`,
  ];
}

async function buildStepbitMessages(prompt) {
  const messages = [
    {
      role: "system",
      content: [
        "You are QuantLab Assistant running inside QuantLab Desktop.",
        "QuantLab is the sovereign research and execution engine.",
        "Stepbit is only the reasoning layer behind this answer.",
        "Be concise, operator-facing, and grounded in the local QuantLab workflow.",
        "Do not invent state changes, launches, promotions, or executions that have not happened.",
        "If you recommend an action, phrase it as a next step inside QuantLab.",
      ].join(" "),
    },
    {
      role: "system",
      content: `Workspace context:\n${buildStepbitContextLines().join("\n")}`,
    },
  ];

  if (/latest failure|failed launch|failed job/i.test(prompt)) {
    const job = getLatestFailedJob();
    if (job) {
      const stderrText = await loadOptionalText(job.stderr_href);
      messages.push({
        role: "system",
        content: `Latest failure context:\n${buildFailureExplanation(job, stderrText)}`,
      });
    }
  }

  messages.push({
    role: "user",
    content: prompt,
  });
  return messages;
}

async function submitStepbitPrompt(prompt, source = "chat") {
  const trimmedPrompt = String(prompt || "").trim();
  if (!trimmedPrompt) return;
  const availability = getStepbitChatAvailability();
  if (!availability.backendReachable) {
    pushMessage("assistant", "Stepbit backend is down. Start Stepbit from QuantLab before using the adapter.", "stepbit");
    return;
  }
  if (!availability.coreReachable) {
    pushMessage("assistant", "Stepbit core is down, so reasoning is unavailable right now. QuantLab actions still work without it.", "stepbit");
    return;
  }

  state.isStepbitSubmitting = true;
  renderChatAdapterStatus();
  pushMessage("assistant", `Routing this ${source} prompt through the Stepbit-backed QuantLab adapter...`, "stepbit");
  try {
    const messages = await buildStepbitMessages(trimmedPrompt);
    const result = await window.quantlabDesktop.askStepbitChat({
      prompt: trimmedPrompt,
      messages,
      search: false,
      reason: false,
    });
    const preface = result.reasoningSeen ? "Stepbit reasoning completed.\n\n" : "";
    pushMessage("assistant", `${preface}${result.content}`, "stepbit");
  } catch (error) {
    pushMessage("assistant", error.message || "Stepbit reasoning failed.", "stepbit");
  } finally {
    state.isStepbitSubmitting = false;
    renderChatAdapterStatus();
  }
}

function handleStepbitPrompt(prompt) {
  const trimmedPrompt = String(prompt || "").trim();
  if (!trimmedPrompt) return;
  pushMessage("user", trimmedPrompt);
  void submitStepbitPrompt(trimmedPrompt, "chat");
}

function askStepbitAboutLatestFailure() {
  const job = getLatestFailedJob();
  if (!job) {
    pushMessage("assistant", "No failed launch job is currently available, so there is nothing to route through Stepbit.", "stepbit");
    return;
  }
  const prompt = "Explain the latest failed launch in QuantLab, summarize the likely root cause, and suggest the next debugging step.";
  pushMessage("user", prompt);
  void submitStepbitPrompt(prompt, "palette");
}

async function handleChatPrompt(prompt) {
  const trimmedPrompt = String(prompt || "").trim();
  if (!trimmedPrompt) return;
  pushMessage("user", trimmedPrompt);
  const stepbitPrompt = extractStepbitPrompt(trimmedPrompt);
  if (stepbitPrompt) {
    await submitStepbitPrompt(stepbitPrompt, "chat");
    return;
  }
  const normalized = trimmedPrompt.toLowerCase();
  if (normalized.includes("open experiments") || normalized.includes("open sweeps") || normalized === "experiments") {
    openExperimentsTab();
    pushMessage("assistant", "Opened the native experiments workspace.");
    return;
  }
  if (normalized.includes("open sweep handoff") || normalized.includes("open sweep decision")) {
    openSweepDecisionTab();
    return;
  }
  if (normalized.includes("refresh experiments") || normalized.includes("refresh sweeps")) {
    refreshExperimentsWorkspace({ focusTab: true, silent: false });
    return;
  }
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
    const runId = extractRunIdAfterPrefix(trimmedPrompt, "mark candidate").trim();
    if (!runId) {
      pushMessage("assistant", "Use `mark candidate <run_id>` to promote a run into the shortlist workflow.");
      return;
    }
    toggleCandidate(runId, true);
    return;
  }
  if (normalized.startsWith("mark baseline")) {
    const runId = extractRunIdAfterPrefix(trimmedPrompt, "mark baseline").trim();
    if (!runId) {
      pushMessage("assistant", "Use `mark baseline <run_id>` to pin the reference run.");
      return;
    }
    setBaseline(runId);
    return;
  }
  const launchRunPayload = parseLaunchRunPrompt(trimmedPrompt);
  if (launchRunPayload) {
    submitLaunchRequest(launchRunPayload, "chat");
    return;
  }
  const launchSweepPayload = parseLaunchSweepPrompt(trimmedPrompt);
  if (launchSweepPayload) {
    submitLaunchRequest(launchSweepPayload, "chat");
    return;
  }
  pushMessage("assistant", "This shell now supports real backend-backed actions. Try:\n- open experiments\n- open sweep handoff\n- launch run ticker ETH-USD start 2023-01-01 end 2024-01-01\n- launch sweep config configs/experiments/eth_2023_grid.yaml\n- open candidates\n- mark candidate <run_id>\n- mark baseline <run_id>\n- open latest run\n- compare selected\n- show artifacts\n- open latest failed launch\n- explain latest failure\n- ask stepbit explain the latest failed launch");
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

async function openExperimentsTab() {
  const current = state.tabs.find((tab) => tab.id === "experiments");
  upsertTab({
    id: "experiments",
    kind: "experiments",
    navKind: "experiments",
    title: "Experiments",
    selectedConfigPath: current?.selectedConfigPath || state.experimentsWorkspace.configs[0]?.path || null,
    selectedSweepId: current?.selectedSweepId || state.experimentsWorkspace.sweeps[0]?.run_id || null,
  });
  await refreshExperimentsWorkspace({ focusTab: true, silent: true });
}

function openSweepDecisionTab(mode = "tracked") {
  const entries = getSweepDecisionCompareEntries();
  if (entries.length < 2) {
    pushMessage("assistant", "Sweep handoff needs at least two tracked rows across the current shortlist or baseline.");
    return;
  }
  upsertTab({
    id: "sweep-decision",
    kind: "sweep-decision",
    navKind: "experiments",
    title: "Sweep Handoff",
    mode,
    rankMetric: "sharpe_simple",
  });
  pushMessage("assistant", "Opened the sweep decision handoff surface.");
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

async function refreshExperimentsWorkspace({ focusTab = false, silent = true } = {}) {
  state.experimentsWorkspace = {
    ...state.experimentsWorkspace,
    status: "loading",
    error: null,
  };
  if (focusTab) renderTabs();
  try {
    const workspace = await buildExperimentsWorkspace();
    state.experimentsWorkspace = {
      status: "ready",
      configs: workspace.configs,
      sweeps: workspace.sweeps,
      error: null,
      updatedAt: new Date().toISOString(),
    };
    const experimentsTab = state.tabs.find((tab) => tab.id === "experiments");
    if (experimentsTab) {
      const nextTab = {
        ...experimentsTab,
        selectedConfigPath: experimentsTab.selectedConfigPath || workspace.configs[0]?.path || null,
        selectedSweepId: experimentsTab.selectedSweepId || workspace.sweeps[0]?.run_id || null,
      };
      if (focusTab) {
        upsertTab(nextTab);
      } else {
        state.tabs = state.tabs.map((tab) => (tab.id === "experiments" ? nextTab : tab));
        if (state.activeTabId === "experiments") renderTabs();
      }
    } else if (focusTab) {
      renderTabs();
    }
    rerenderContextualTabs();
    if (!silent) {
      pushMessage(
        "assistant",
        `Refreshed experiments workspace: ${workspace.configs.length} configs and ${workspace.sweeps.length} recent sweeps.`,
      );
    }
  } catch (error) {
    state.experimentsWorkspace = {
      ...state.experimentsWorkspace,
      status: "error",
      error: error.message || "Could not refresh the experiments workspace.",
    };
    if (focusTab) renderTabs();
    if (!silent) pushMessage("assistant", state.experimentsWorkspace.error);
  }
}

async function buildExperimentsWorkspace() {
  const [configsListing, sweepsListing] = await Promise.all([
    window.quantlabDesktop.listDirectory(CONFIG.experimentsConfigDir, 0),
    window.quantlabDesktop.listDirectory(CONFIG.sweepsOutputDir, 0),
  ]);

  const configEntries = (configsListing.entries || [])
    .filter((entry) => entry.kind === "file" && /\.ya?ml$/i.test(entry.name))
    .sort((left, right) => String(right.modified_at || "").localeCompare(String(left.modified_at || "")))
    .slice(0, CONFIG.maxExperimentsConfigs);

  const configs = await Promise.all(configEntries.map(async (entry) => ({
    name: entry.name,
    path: entry.path,
    relativePath: entry.relative_path || entry.name,
    modifiedAt: entry.modified_at,
    sizeBytes: entry.size_bytes,
    previewText: await loadExperimentConfigPreview(entry.path),
  })));

  const sweepDirectories = (sweepsListing.entries || [])
    .filter((entry) => entry.kind === "directory" && entry.depth === 0)
    .sort((left, right) => String(right.modified_at || "").localeCompare(String(left.modified_at || "")))
    .slice(0, CONFIG.maxRecentSweeps);

  const sweeps = await Promise.all(sweepDirectories.map((entry) => buildSweepSummary(entry)));
  return {
    configs,
    sweeps: sweeps.filter(Boolean),
  };
}

async function buildSweepSummary(entry) {
  const rootPath = entry.path;
  const fileListing = await window.quantlabDesktop.listDirectory(rootPath, 0).catch(() => ({ entries: [], truncated: false }));
  const metaPath = `${rootPath}\\meta.json`;
  const leaderboardPath = `${rootPath}\\leaderboard.csv`;
  const experimentsPath = `${rootPath}\\experiments.csv`;
  const walkforwardSummaryPath = `${rootPath}\\walkforward_summary.csv`;
  const configResolvedPath = `${rootPath}\\config_resolved.yaml`;

  const [meta, leaderboardText, experimentsText, walkforwardText] = await Promise.all([
    readOptionalProjectJson(metaPath),
    readOptionalProjectText(leaderboardPath),
    readOptionalProjectText(experimentsPath),
    readOptionalProjectText(walkforwardSummaryPath),
  ]);

  const leaderboardRows = parseCsvPreviewRows(leaderboardText, CONFIG.maxSweepRows);
  const walkforwardRows = parseCsvPreviewRows(walkforwardText, CONFIG.maxSweepRows);
  const experimentsRows = parseCsvPreviewRows(experimentsText, 1);
  const firstRow = leaderboardRows[0] || experimentsRows[0] || null;
  const decisionRows = buildSweepDecisionRows(
    meta?.run_id || basenameValue(rootPath),
    meta?.config_path || "",
    Array.isArray(meta?.top10) && meta.top10.length ? meta.top10.slice(0, CONFIG.maxSweepRows) : leaderboardRows,
  );

  return {
    run_id: meta?.run_id || basenameValue(rootPath),
    path: rootPath,
    modifiedAt: entry.modified_at,
    createdAt: meta?.created_at || entry.modified_at,
    mode: meta?.mode || inferSweepModeFromName(entry.name),
    configPath: meta?.config_path || "",
    configName: basenameValue(meta?.config_path || ""),
    nRuns: meta?.n_runs ?? meta?.n_train_runs ?? null,
    nSelected: meta?.n_selected ?? null,
    nTrainRuns: meta?.n_train_runs ?? null,
    nTestRuns: meta?.n_test_runs ?? null,
    topResults: Array.isArray(meta?.top10) ? meta.top10.slice(0, CONFIG.maxSweepRows) : [],
    decisionRows,
    leaderboardRows,
    walkforwardRows,
    files: fileListing.entries || [],
    filesTruncated: Boolean(fileListing.truncated),
    metaPath,
    leaderboardPath,
    experimentsPath,
    walkforwardSummaryPath,
    configResolvedPath,
    headlineReturn: coerceNumber(firstRow?.total_return),
    headlineSharpe: coerceNumber(firstRow?.sharpe_simple || firstRow?.best_test_sharpe),
    headlineDrawdown: coerceNumber(firstRow?.max_drawdown),
  };
}

async function readOptionalProjectText(targetPath) {
  try {
    return await window.quantlabDesktop.readProjectText(targetPath);
  } catch (_error) {
    return "";
  }
}

async function readOptionalProjectJson(targetPath) {
  try {
    return await window.quantlabDesktop.readProjectJson(targetPath);
  } catch (_error) {
    return null;
  }
}

function coerceNumber(value) {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const parsed = Number(String(value ?? "").trim());
  return Number.isFinite(parsed) ? parsed : null;
}

function inferSweepModeFromName(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("walkforward")) return "walkforward";
  if (normalized.includes("grid")) return "grid";
  return "sweep";
}

async function loadExperimentConfigPreview(configPath) {
  if (!configPath) return "";
  if (state.experimentConfigPreviewCache.has(configPath)) {
    return state.experimentConfigPreviewCache.get(configPath);
  }
  const raw = await readOptionalProjectText(configPath);
  const previewText = raw ? raw.split(/\r?\n/).slice(0, 48).join("\n") : "";
  if (previewText) state.experimentConfigPreviewCache.set(configPath, previewText);
  return previewText;
}

function buildSweepDecisionRows(sweepRunId, configPath, rows) {
  return (rows || []).map((row, index) => {
    const totalReturn = coerceNumber(row?.total_return);
    const sharpe = coerceNumber(row?.sharpe_simple ?? row?.best_test_sharpe);
    const drawdown = coerceNumber(row?.max_drawdown);
    const trades = coerceNumber(row?.trades ?? row?.n_test_runs);
    return {
      entry_id: `${sweepRunId}:leaderboard:${index}`,
      sweep_run_id: sweepRunId,
      source: "leaderboard",
      row_index: index,
      config_path: configPath || "",
      total_return: totalReturn,
      sharpe_simple: sharpe,
      max_drawdown: drawdown,
      trades,
      label: `Row #${index + 1}`,
      row_snapshot: row,
    };
  });
}

function closeTab(tabId) {
  state.tabs = state.tabs.filter((tab) => tab.id !== tabId);
  if (state.activeTabId === tabId) state.activeTabId = state.tabs[0]?.id || null;
  renderTabs();
  scheduleShellWorkspacePersist();
}

function syncNav(kind) {
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("is-active"));
  const mapping = { chat: "open-chat", experiments: "open-experiments", launch: "open-launch", runs: "open-runs", candidates: "open-candidates", compare: "open-compare", ops: "open-ops" };
  const target = document.querySelector(`.nav-item[data-action="${mapping[kind] || "open-chat"}"]`);
  if (target) target.classList.add("is-active");
}

function pushMessage(role, content, label = role) {
  state.chatMessages.push({ role, content, label });
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

function renderExperimentsTab(tab) {
  return renderExperimentsTabView(tab, getRendererContext());
}

function renderSweepDecisionTab(tab) {
  return renderSweepDecisionTabView(tab, getRendererContext());
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
    experimentsWorkspace: state.experimentsWorkspace,
    sweepDecisionStore: state.sweepDecisionStore,
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
    findSweep,
    findSweepDecisionRow,
    findJob,
    getRuns,
    getJobs,
    getLatestRun,
    getLatestFailedJob,
    getDecisionCompareRunIds,
    getRunRelatedJobs,
    getSweepDecisionEntriesResolved,
    getSweepDecisionEntriesForRun,
    getSweepDecisionCompareEntries,
    sweepDecision: {
      getEntry: (store, entryId) => sweepDecisionStore.getSweepDecisionEntry(store, entryId),
      getEntriesResolved: (store, findRowFn) => sweepDecisionStore.getSweepDecisionEntriesResolved(store, findRowFn),
      isTracked: (store, entryId) => sweepDecisionStore.isTrackedSweepEntry(store, entryId),
      isShortlisted: (store, entryId) => sweepDecisionStore.isShortlistedSweepEntry(store, entryId),
      isBaseline: (store, entryId) => sweepDecisionStore.isBaselineSweepEntry(store, entryId),
      summarizeState: (store, entryId) => sweepDecisionStore.summarizeSweepDecisionState(store, entryId),
    },
    buildFailureExplanation,
  };
}

function upsertTab(nextTab) {
  const index = state.tabs.findIndex((tab) => tab.id === nextTab.id);
  if (index >= 0) state.tabs[index] = { ...state.tabs[index], ...nextTab };
  else state.tabs.push(nextTab);
  state.activeTabId = nextTab.id;
  renderTabs();
  scheduleShellWorkspacePersist();
}

function rerenderContextualTabs() {
  if (state.tabs.some((tab) => ["experiments", "sweep-decision", "run", "compare", "artifacts", "candidates", "paper", "job"].includes(tab.kind))) renderTabs();
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
  scheduleShellWorkspacePersist();
}

function getBrowserUrlForActiveContext() {
  if (!state.workspace.serverUrl) return "";
  const activeTab = state.tabs.find((tab) => tab.id === state.activeTabId);
  if (activeTab?.kind === "iframe") return activeTab.url;
  if (activeTab?.kind === "experiments") return `${state.workspace.serverUrl}/research_ui/index.html#/launch`;
  if (activeTab?.kind === "sweep-decision") return `${state.workspace.serverUrl}/research_ui/index.html#/launch`;
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

function defaultSweepDecisionStore() {
  return sweepDecisionStore.defaultSweepDecisionStore();
}

function normalizeSweepDecisionStore(store) {
  return sweepDecisionStore.normalizeSweepDecisionStore(store);
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

function getSweepDecisionEntries() {
  return sweepDecisionStore.getSweepDecisionEntries(state.sweepDecisionStore);
}

function getSweepDecisionEntry(entryId) {
  return sweepDecisionStore.getSweepDecisionEntry(state.sweepDecisionStore, entryId);
}

function getSweepDecisionResolvedEntry(entryId) {
  return sweepDecisionStore.getSweepDecisionEntriesResolved(state.sweepDecisionStore, findSweepDecisionRow)
    .find((entry) => entry.entry_id === entryId) || null;
}

function getSweepDecisionEntriesResolved() {
  return sweepDecisionStore.getSweepDecisionEntriesResolved(state.sweepDecisionStore, findSweepDecisionRow);
}

function isTrackedSweepEntry(entryId) {
  return sweepDecisionStore.isTrackedSweepEntry(state.sweepDecisionStore, entryId);
}

function isShortlistedSweepEntry(entryId) {
  return sweepDecisionStore.isShortlistedSweepEntry(state.sweepDecisionStore, entryId);
}

function isBaselineSweepEntry(entryId) {
  return sweepDecisionStore.isBaselineSweepEntry(state.sweepDecisionStore, entryId);
}

function getSweepDecisionCompareEntries() {
  return sweepDecisionStore.getSweepDecisionCompareEntries(
    state.sweepDecisionStore,
    findSweepDecisionRow,
    CONFIG.maxSweepDecisionCompare,
  );
}

function getRunRelatedJobs(runId) {
  return getJobs()
    .filter((job) => job.run_id === runId)
    .sort((left, right) => String(right.created_at || "").localeCompare(String(left.created_at || "")));
}

function getSweepDecisionEntriesForRun(runId) {
  return getSweepDecisionEntriesResolved().filter((entry) => entry.sweep_run_id === runId);
}

function findRun(runId) {
  return getRuns().find((run) => run.run_id === runId) || null;
}

function findJob(requestId) {
  return getJobs().find((job) => job.request_id === requestId) || null;
}

function findSweep(sweepRunId) {
  return (state.experimentsWorkspace.sweeps || []).find((sweep) => sweep.run_id === sweepRunId) || null;
}

function findSweepDecisionRow(entryId) {
  for (const sweep of state.experimentsWorkspace.sweeps || []) {
    const row = (sweep.decisionRows || []).find((item) => item.entry_id === entryId);
    if (row) {
      return {
        ...row,
        sweep: {
          run_id: sweep.run_id,
          mode: sweep.mode,
          path: sweep.path,
          configPath: sweep.configPath,
          configName: sweep.configName,
        },
      };
    }
  }
  return null;
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

async function saveSweepDecisionStore(nextStore, message = "") {
  try {
    state.sweepDecisionStore = normalizeSweepDecisionStore(await window.quantlabDesktop.saveSweepDecisionStore(nextStore));
    rerenderContextualTabs();
    if (message) pushMessage("assistant", message);
  } catch (error) {
    pushMessage("assistant", error.message || "Could not persist the sweep decision handoff store.");
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

async function toggleSweepDecisionEntry(row, forceValue = null) {
  if (!row?.entry_id || !row?.sweep_run_id) return;
  const existing = getSweepDecisionEntry(row.entry_id);
  const shouldExist = forceValue === null ? !existing : Boolean(forceValue);
  const entries = getSweepDecisionEntries().filter((entry) => entry.entry_id !== row.entry_id);
  if (shouldExist) {
    entries.push({
      entry_id: row.entry_id,
      sweep_run_id: row.sweep_run_id,
      source: row.source || "leaderboard",
      row_index: row.row_index || 0,
      note: existing?.note || "",
      shortlisted: existing?.shortlisted || false,
      config_path: row.config_path || row.sweep?.configPath || "",
      row_snapshot: row.row_snapshot || row,
      created_at: existing?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  }
  const nextStore = {
    ...state.sweepDecisionStore,
    entries,
    baseline_entry_id:
      shouldExist || state.sweepDecisionStore.baseline_entry_id !== row.entry_id
        ? state.sweepDecisionStore.baseline_entry_id
        : null,
  };
  await saveSweepDecisionStore(
    nextStore,
    shouldExist
      ? `Tracked ${row.entry_id} in the sweep handoff.`
      : `Removed ${row.entry_id} from the sweep handoff.`,
  );
}

async function toggleSweepDecisionShortlist(entryId) {
  const resolved = getSweepDecisionResolvedEntry(entryId);
  if (!resolved?.row) {
    pushMessage("assistant", `Sweep row ${entryId} is no longer available in the current experiments workspace.`);
    return;
  }
  const existing = getSweepDecisionEntry(entryId);
  const entries = getSweepDecisionEntries().filter((entry) => entry.entry_id !== entryId);
  entries.push({
    entry_id: resolved.entry_id,
    sweep_run_id: resolved.sweep_run_id,
    source: resolved.source,
    row_index: resolved.row_index,
    note: existing?.note || "",
    shortlisted: !existing?.shortlisted,
    config_path: resolved.config_path || resolved.row?.config_path || "",
    row_snapshot: resolved.row_snapshot || resolved.row,
    created_at: existing?.created_at || new Date().toISOString(),
    updated_at: new Date().toISOString(),
  });
  await saveSweepDecisionStore(
    {
      ...state.sweepDecisionStore,
      entries,
    },
    existing?.shortlisted
      ? `Removed ${entryId} from the sweep shortlist.`
      : `Added ${entryId} to the sweep shortlist.`,
  );
}

async function setSweepDecisionBaseline(entryId) {
  const resolved = getSweepDecisionResolvedEntry(entryId);
  if (!resolved?.row) {
    pushMessage("assistant", `Sweep row ${entryId} is no longer available in the current experiments workspace.`);
    return;
  }
  const nextBaseline = state.sweepDecisionStore.baseline_entry_id === entryId ? null : entryId;
  const existing = getSweepDecisionEntry(entryId);
  const entries = getSweepDecisionEntries().filter((entry) => entry.entry_id !== entryId);
  if (nextBaseline) {
    entries.push({
      entry_id: resolved.entry_id,
      sweep_run_id: resolved.sweep_run_id,
      source: resolved.source,
      row_index: resolved.row_index,
      note: existing?.note || "",
      shortlisted: existing?.shortlisted || false,
      config_path: resolved.config_path || resolved.row?.config_path || "",
      row_snapshot: resolved.row_snapshot || resolved.row,
      created_at: existing?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  } else if (existing) {
    entries.push(existing);
  }
  await saveSweepDecisionStore(
    {
      ...state.sweepDecisionStore,
      baseline_entry_id: nextBaseline,
      entries,
    },
    nextBaseline
      ? `Pinned ${entryId} as the sweep handoff baseline.`
      : "Cleared the sweep handoff baseline.",
  );
}

async function editSweepDecisionNote(entryId) {
  const existing = getSweepDecisionEntry(entryId);
  const resolved = getSweepDecisionResolvedEntry(entryId);
  if (!resolved?.row) {
    pushMessage("assistant", `Sweep row ${entryId} is no longer available in the current experiments workspace.`);
    return;
  }
  const nextNote = window.prompt(`Sweep handoff note for ${entryId}`, existing?.note || "");
  if (nextNote === null) return;
  const entries = getSweepDecisionEntries().filter((entry) => entry.entry_id !== entryId);
  entries.push({
    entry_id: resolved.entry_id,
    sweep_run_id: resolved.sweep_run_id,
    source: resolved.source,
    row_index: resolved.row_index,
    note: nextNote.trim(),
    shortlisted: existing?.shortlisted || false,
    config_path: resolved.config_path || resolved.row?.config_path || "",
    row_snapshot: resolved.row_snapshot || resolved.row,
    created_at: existing?.created_at || new Date().toISOString(),
    updated_at: new Date().toISOString(),
  });
  await saveSweepDecisionStore(
    {
      ...state.sweepDecisionStore,
      entries,
    },
    nextNote.trim()
      ? `Updated the sweep note for ${entryId}.`
      : `Cleared the sweep note for ${entryId}.`,
  );
}

function summarizeCandidateState(runId) {
  return decisionStore.summarizeCandidateState(state.candidatesStore, runId);
}

function openRunDecisionCompare(runId) {
  const relatedRunIds = uniqueRunIds([runId, ...getDecisionCompareRunIds().filter((candidateId) => candidateId !== runId)]);
  if (relatedRunIds.length < 2) {
    pushMessage("assistant", "Run compare needs this run plus at least one baseline or shortlisted peer.");
    return;
  }
  openCompareSelectionTab(relatedRunIds.slice(0, CONFIG.maxCandidateCompare), "decision-linked runs");
}

function openLatestRelatedLaunchJobForRun(runId) {
  const relatedJob = getRunRelatedJobs(runId)[0] || null;
  if (!relatedJob?.request_id) {
    pushMessage("assistant", `Run ${runId} does not currently expose a linked launch job.`);
    return;
  }
  openJobTab(relatedJob.request_id);
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
  container.querySelectorAll("[data-open-decision-compare]").forEach((button) => {
    button.addEventListener("click", () => openRunDecisionCompare(button.dataset.openDecisionCompare || runId));
  });
  container.querySelectorAll("[data-open-related-job]").forEach((button) => {
    button.addEventListener("click", () => openLatestRelatedLaunchJobForRun(button.dataset.openRelatedJob || runId));
  });
  container.querySelectorAll("[data-open-sweep-handoff]").forEach((button) => {
    button.addEventListener("click", () => openSweepDecisionTab(button.dataset.openSweepHandoff || "tracked"));
  });
  container.querySelectorAll("[data-open-candidates]").forEach((button) => {
    button.addEventListener("click", () => openCandidatesTab());
  });
  container.querySelectorAll("[data-open-job-link]").forEach((button) => {
    button.addEventListener("click", () => {
      const url = absoluteUrl(button.dataset.openJobLink);
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
