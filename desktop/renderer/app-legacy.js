// @ts-check

import * as decisionStore from "./modules/decision-store.js";
import {
  NAV_ACTION_BY_KIND,
  PALETTE_ACTION_SPECS,
  SHELL_COPY,
} from "./modules/shell-chrome.js";
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
  LruCache,
  uniqueRunIds as dedupeRunIds,
} from "./modules/utils.js";
import {
  renderArtifactsTab as renderArtifactsTabView,
  renderCandidatesTab as renderCandidatesTabView,
  renderCompareTab as renderCompareTabView,
  renderExperimentsTab as renderExperimentsTabView,
  renderJobTab as renderJobTabView,
  renderPaperOpsTab as renderPaperOpsTabView,
  renderRunsTab as renderRunsTabView,
  renderRunTab as renderRunTabView,
  renderSystemTab as renderSystemTabView,
  renderSweepDecisionTab as renderSweepDecisionTabView,
} from "./modules/tab-renderers.js";

/** @typedef {import("../shared/models/runtime").RuntimeStatus} RuntimeStatus */
/** @typedef {import("../shared/models/runtime").RuntimeChipState} RuntimeChipState */
/** @typedef {import("../shared/models/snapshot").SnapshotStatus} SnapshotStatus */
/** @typedef {import("../shared/models/snapshot").SnapshotSource} SnapshotSource */
/** @typedef {import("../shared/models/workspace").WorkspaceState} WorkspaceState */
/** @typedef {import("../shared/ipc/bridge").QuantlabDesktopBridge} QuantlabDesktopBridge */

/** @type {QuantlabDesktopBridge} */
const desktopBridge = window.quantlabDesktop;

const CONFIG = {
  runsIndexPath: "/outputs/runs/runs_index.json",
  localRunsIndexPath: "outputs/runs/runs_index.json",
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
  maxDetailCacheEntries: 50,
  maxConsecutiveRefreshErrors: 3,
  maxSurfaceTabs: 7,
};

let unsubscribeWorkspaceState = null;

const state = {
  /** @type {WorkspaceState} */
  workspace: { status: "starting", serverUrl: null, logs: [], error: null, source: null },
  snapshot: null,
  candidatesStore: defaultCandidatesStore(),
  candidatesLoaded: false,
  sweepDecisionStore: defaultSweepDecisionStore(),
  sweepDecisionLoaded: false,
  selectedRunIds: [],
  detailCache: new LruCache(CONFIG.maxDetailCacheEntries),
  experimentsWorkspace: { status: "idle", configs: [], sweeps: [], error: null, updatedAt: null },
  experimentConfigPreviewCache: new Map(),
  isSubmittingLaunch: false,
  launchFeedback: SHELL_COPY.defaultLaunchFeedback,
  refreshTimer: null,
  isStepbitSubmitting: false,
  /** @type {SnapshotStatus} */
  snapshotStatus: {
    status: "idle",
    error: null,
    source: "none",
    lastSuccessAt: null,
    consecutiveErrors: 0,
    refreshPaused: false,
  },
  isRetryingWorkspace: false,
  chatMessages: [
    {
      role: "assistant",
      label: "quantlab",
      content: SHELL_COPY.assistantWelcome,
    },
  ],
  tabs: [],
  activeTabId: null,
  initialSurfaceResolved: false,
  paletteOpen: false,
  paletteQuery: "",
  workspaceStoreLoaded: false,
  workspacePersistTimer: null,
};

const WORKBENCH_PRIORITY_KINDS = new Set([
  "runs",
  "run",
  "compare",
  "candidates",
  "artifacts",
  "paper",
  "system",
  "experiments",
  "sweep-decision",
  "job",
]);

const elements = {
  runtimeSummary: /** @type {HTMLDivElement} */ (document.getElementById("runtime-summary")),
  runtimeMeta: /** @type {HTMLDivElement} */ (document.getElementById("runtime-meta")),
  runtimeAlert: /** @type {HTMLDivElement} */ (document.getElementById("runtime-alert")),
  runtimeRetry: /** @type {HTMLButtonElement} */ (document.getElementById("runtime-retry")),
  runtimeChips: /** @type {HTMLDivElement} */ (document.getElementById("runtime-chips")),
  topbarEyebrow: /** @type {HTMLDivElement} */ (document.getElementById("topbar-eyebrow")),
  chatLog: /** @type {HTMLDivElement} */ (document.getElementById("chat-log")),
  chatForm: /** @type {HTMLFormElement} */ (document.getElementById("chat-form")),
  chatInput: /** @type {HTMLTextAreaElement} */ (document.getElementById("chat-input")),
  chatStepbit: /** @type {HTMLButtonElement} */ (document.getElementById("chat-stepbit")),
  chatAdapterStatus: /** @type {HTMLDivElement} */ (document.getElementById("chat-adapter-status")),
  tabsBar: /** @type {HTMLDivElement} */ (document.getElementById("tabs-bar")),
  tabContent: /** @type {HTMLDivElement} */ (document.getElementById("tab-content")),
  topbarTitle: /** @type {HTMLHeadingElement} */ (document.getElementById("topbar-title")),
  topbarSurfaceChip: /** @type {HTMLDivElement} */ (document.getElementById("topbar-surface-chip")),
  topbarRuntimeChip: /** @type {HTMLDivElement} */ (document.getElementById("topbar-runtime-chip")),
  topbarServerChip: /** @type {HTMLDivElement} */ (document.getElementById("topbar-server-chip")),
  paletteSearch: /** @type {HTMLInputElement} */ (document.getElementById("palette-search")),
  paletteInput: /** @type {HTMLInputElement} */ (document.getElementById("palette-input")),
  runCommand: /** @type {HTMLButtonElement} */ (document.getElementById("run-command")),
  commandPaletteTrigger: /** @type {HTMLButtonElement} */ (document.getElementById("command-palette-trigger")),
  openBrowserRuns: /** @type {HTMLButtonElement} */ (document.getElementById("open-browser-runs")),
  paletteOverlay: /** @type {HTMLDivElement} */ (document.getElementById("palette-overlay")),
  closePalette: /** @type {HTMLButtonElement} */ (document.getElementById("close-palette")),
  paletteResults: /** @type {HTMLDivElement} */ (document.getElementById("palette-results")),
  workflowLaunchForm: /** @type {HTMLFormElement} */ (document.getElementById("workflow-launch-form")),
  workflowLaunchCommand: /** @type {HTMLSelectElement} */ (document.getElementById("workflow-launch-command")),
  workflowRunFields: /** @type {HTMLDivElement} */ (document.getElementById("workflow-run-fields")),
  workflowSweepFields: /** @type {HTMLDivElement} */ (document.getElementById("workflow-sweep-fields")),
  workflowLaunchTicker: /** @type {HTMLInputElement} */ (document.getElementById("workflow-launch-ticker")),
  workflowLaunchStart: /** @type {HTMLInputElement} */ (document.getElementById("workflow-launch-start")),
  workflowLaunchEnd: /** @type {HTMLInputElement} */ (document.getElementById("workflow-launch-end")),
  workflowLaunchInterval: /** @type {HTMLInputElement} */ (document.getElementById("workflow-launch-interval")),
  workflowLaunchCash: /** @type {HTMLInputElement} */ (document.getElementById("workflow-launch-cash")),
  workflowLaunchPaper: /** @type {HTMLInputElement} */ (document.getElementById("workflow-launch-paper")),
  workflowLaunchConfigPath: /** @type {HTMLInputElement} */ (document.getElementById("workflow-launch-config-path")),
  workflowLaunchOutDir: /** @type {HTMLInputElement} */ (document.getElementById("workflow-launch-out-dir")),
  workflowLaunchMeta: /** @type {HTMLDivElement} */ (document.getElementById("workflow-launch-meta")),
  workflowLaunchFeedback: /** @type {HTMLDivElement} */ (document.getElementById("workflow-launch-feedback")),
  workflowLaunchSubmit: /** @type {HTMLButtonElement} */ (document.getElementById("workflow-launch-submit")),
  workflowJobsList: /** @type {HTMLDivElement} */ (document.getElementById("workflow-jobs-list")),
  workflowRunsMeta: /** @type {HTMLDivElement} */ (document.getElementById("workflow-runs-meta")),
  workflowRunsList: /** @type {HTMLDivElement} */ (document.getElementById("workflow-runs-list")),
  workflowOpenCompare: /** @type {HTMLButtonElement} */ (document.getElementById("workflow-open-compare")),
  workflowClearSelection: /** @type {HTMLButtonElement} */ (document.getElementById("workflow-clear-selection")),
  workspaceGrid: /** @type {HTMLElement} */ (document.querySelector(".workspace-grid")),
};

const paletteActions = PALETTE_ACTION_SPECS.map((action) => ({
  ...action,
  run: buildPaletteActionHandler(action.handler),
}));

document.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  try {
    restoreShellWorkspaceStore(await desktopBridge.getShellWorkspaceStore());
  } catch (_error) {
    // Workspace restore is optional; the shell can still boot from a cold state.
  } finally {
    state.workspaceStoreLoaded = true;
  }
  renderAll();
  try {
    state.candidatesStore = normalizeCandidatesStore(await desktopBridge.getCandidatesStore());
  } catch (_error) {
    state.candidatesStore = defaultCandidatesStore();
  } finally {
    state.candidatesLoaded = true;
  }
  try {
    state.sweepDecisionStore = normalizeSweepDecisionStore(await desktopBridge.getSweepDecisionStore());
  } catch (_error) {
    state.sweepDecisionStore = defaultSweepDecisionStore();
  } finally {
    state.sweepDecisionLoaded = true;
  }
  const initialState = await desktopBridge.getWorkspaceState();
  state.workspace = initialState;
  await refreshSnapshot();
  renderWorkspaceState();
  renderWorkflow();
  unsubscribeWorkspaceState = desktopBridge.onWorkspaceState((payload) => {
    state.workspace = payload;
    renderWorkspaceState();
    if (payload.serverUrl) ensureRefreshLoop();
  });
  if (initialState.serverUrl) ensureRefreshLoop();
});

window.addEventListener("beforeunload", () => {
  stopRefreshLoop();
  if (state.workspacePersistTimer) window.clearTimeout(state.workspacePersistTimer);
  if (unsubscribeWorkspaceState) {
    unsubscribeWorkspaceState();
    unsubscribeWorkspaceState = null;
  }
  if (state.workspaceStoreLoaded) {
    desktopBridge.saveShellWorkspaceStore(serializeShellWorkspaceStore()).catch(() => {});
  }
});

function bindEvents() {
  document.querySelectorAll("[data-action]").forEach((button) => {
    const actionButton = /** @type {HTMLElement} */ (button);
    actionButton.addEventListener("click", () => {
      const action = actionButton.dataset.action;
      if (action === "open-assistant") focusAssistant();
      if (action === "open-system") openSystemTab();
      if (action === "open-experiments") openExperimentsTab();
      if (action === "open-runs") openRunsNativeTab();
      if (action === "open-candidates") openCandidatesTab();
      if (action === "open-compare") openCompareSelectionTab();
      if (action === "open-ops") openPaperOpsTab();
    });
  });
  document.querySelectorAll("[data-prompt]").forEach((button) => {
    const promptButton = /** @type {HTMLElement} */ (button);
    promptButton.addEventListener("click", () => {
      const prompt = promptButton.dataset.prompt || "";
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
    elements.paletteInput.value = "";
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
  if (!state.workspace.serverUrl) return;
  refreshSnapshot();
  if (!state.refreshTimer) state.refreshTimer = window.setInterval(refreshSnapshot, CONFIG.refreshIntervalMs);
}

function stopRefreshLoop() {
  if (state.refreshTimer) {
    window.clearInterval(state.refreshTimer);
    state.refreshTimer = null;
  }
}

async function refreshSnapshot() {
  try {
    const { runsRegistry, source, primaryError } = await loadRunsRegistrySnapshot();
    if (!state.workspace.serverUrl) stopRefreshLoop();
    state.detailCache.clear();
    const optionalErrors = [];
    if (primaryError?.message) optionalErrors.push(primaryError.message);
    const extra = state.workspace.serverUrl
      ? await Promise.allSettled([
        window.quantlabDesktop.requestJson(CONFIG.launchControlPath),
        window.quantlabDesktop.requestJson(CONFIG.paperHealthPath),
        window.quantlabDesktop.requestJson(CONFIG.brokerHealthPath),
        window.quantlabDesktop.requestJson(CONFIG.stepbitWorkspacePath),
      ])
      : [];
    extra.forEach((result) => {
      if (result.status === "rejected" && result.reason?.message) optionalErrors.push(result.reason.message);
    });
    state.snapshot = {
      runsRegistry,
      launchControl: extra[0]?.status === "fulfilled" ? extra[0].value : state.snapshot?.launchControl || null,
      paperHealth: extra[1]?.status === "fulfilled" ? extra[1].value : state.snapshot?.paperHealth || null,
      brokerHealth: extra[2]?.status === "fulfilled" ? extra[2].value : state.snapshot?.brokerHealth || null,
      stepbitWorkspace: extra[3]?.status === "fulfilled" ? extra[3].value : state.snapshot?.stepbitWorkspace || null,
    };
    state.snapshotStatus = {
      status: optionalErrors.length || source === "local" ? "degraded" : "ok",
      error: optionalErrors[0] || null,
      source,
      lastSuccessAt: new Date().toISOString(),
      consecutiveErrors: 0,
      refreshPaused: false,
    };
    const validIds = new Set(getRuns().map((run) => run.run_id));
    const filteredSelection = state.selectedRunIds.filter((runId) => validIds.has(runId));
    if (filteredSelection.length !== state.selectedRunIds.length) {
      state.selectedRunIds = filteredSelection;
      scheduleShellWorkspacePersist();
    }
    reconcileWorkspaceTabs();
    renderWorkspaceState();
    renderWorkflow();
    maybeOpenDefaultSurface();
    refreshLiveJobTabs();
    rerenderContextualTabs();
    if (state.tabs.some((tab) => ["experiments", "sweep-decision"].includes(tab.kind))) {
      refreshExperimentsWorkspace({ focusTab: false, silent: true });
    }
  } catch (error) {
    const consecutiveErrors = (state.snapshotStatus.consecutiveErrors || 0) + 1;
    const refreshPaused = consecutiveErrors >= CONFIG.maxConsecutiveRefreshErrors;
    if (refreshPaused) stopRefreshLoop();
    state.snapshotStatus = {
      status: "error",
      error: error?.message || "The local API is unavailable.",
      source: "none",
      lastSuccessAt: state.snapshotStatus.lastSuccessAt,
      consecutiveErrors,
      refreshPaused,
    };
    renderWorkspaceState();
    // Keep the shell usable even if optional surfaces are down.
  }
}

/**
 * @returns {Promise<{ runsRegistry: any, source: SnapshotSource, primaryError: Error | null }>}
 */
async function loadRunsRegistrySnapshot() {
  /** @type {Error | null} */
  let primaryError = null;
  if (state.workspace.serverUrl) {
    try {
      const runsRegistry = await window.quantlabDesktop.requestJson(CONFIG.runsIndexPath);
      /** @type {SnapshotSource} */
      const source = "api";
      return { runsRegistry, source, primaryError: null };
    } catch (error) {
      primaryError = /** @type {Error} */ (error);
    }
  }
  const runsRegistry = await window.quantlabDesktop.readProjectJson(CONFIG.localRunsIndexPath);
  /** @type {SnapshotSource} */
  const source = "local";
  return { runsRegistry, source, primaryError };
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
    if (tab.url.includes(":8000/research_ui")) return null;
    return { ...base, url: tab.url };
  }
  if (base.kind === "run" || base.kind === "artifacts") {
    if (typeof tab.runId !== "string" || !tab.runId) return null;
    return { ...base, runId: tab.runId };
  }
  if (base.kind === "runs" || base.kind === "paper" || base.kind === "system") return base;
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
  state.initialSurfaceResolved = restored.tabs.length > 0;
  state.selectedRunIds = restored.selected_run_ids;
  applyLaunchFormState(restored.launch_form);
}

function resolveExperimentConfigPath(selectedConfigPath, configs) {
  const configEntries = Array.isArray(configs) ? configs : [];
  if (!configEntries.length) return null;
  return configEntries.some((entry) => entry.path === selectedConfigPath)
    ? selectedConfigPath
    : configEntries[0]?.path || null;
}

function resolveExperimentSweepId(selectedSweepId, sweeps) {
  const sweepEntries = Array.isArray(sweeps) ? sweeps : [];
  if (!sweepEntries.length) return null;
  const selectedSweep = sweepEntries.find((entry) => entry.run_id === selectedSweepId) || null;
  const preferredSweep = sweepEntries.find((entry) => entry.hasStructuredData) || sweepEntries[0] || null;
  if (selectedSweep?.hasStructuredData) return selectedSweepId;
  if (selectedSweep && !preferredSweep?.hasStructuredData) return selectedSweepId;
  return preferredSweep?.run_id || null;
}

function reconcileWorkspaceTabs() {
  if (!state.tabs.length) return false;

  const validRunIds = new Set(getRuns().map((run) => run.run_id));
  const validJobIds = new Set(getJobs().map((job) => job.request_id));
  const experimentsReady = state.experimentsWorkspace.status === "ready";
  let changed = false;

  const nextTabs = state.tabs
    .map((tab) => {
      if (tab.kind === "run" || tab.kind === "artifacts") {
        if (!validRunIds.has(tab.runId)) {
          changed = true;
          return null;
        }
        return tab;
      }

      if (tab.kind === "compare") {
        const runIds = uniqueRunIds((tab.runIds || []).filter((runId) => validRunIds.has(runId))).slice(0, CONFIG.maxCandidateCompare);
        if (runIds.length < 2) {
          changed = true;
          return null;
        }
        if (
          runIds.length !== (tab.runIds || []).length
          || runIds.some((runId, index) => runId !== tab.runIds[index])
        ) {
          changed = true;
          return { ...tab, runIds };
        }
        return tab;
      }

      if (tab.kind === "job") {
        if (!validJobIds.has(tab.requestId)) {
          changed = true;
          return null;
        }
        return tab;
      }

      if (tab.kind === "experiments" && experimentsReady) {
        const selectedConfigPath = resolveExperimentConfigPath(tab.selectedConfigPath, state.experimentsWorkspace.configs);
        const selectedSweepId = resolveExperimentSweepId(tab.selectedSweepId, state.experimentsWorkspace.sweeps);
        if (selectedConfigPath !== tab.selectedConfigPath || selectedSweepId !== tab.selectedSweepId) {
          changed = true;
          return {
            ...tab,
            selectedConfigPath,
            selectedSweepId,
          };
        }
      }

      return tab;
    })
    .filter(Boolean);

  const nextActiveTabId = nextTabs.some((tab) => tab.id === state.activeTabId) ? state.activeTabId : nextTabs[0]?.id || null;
  if (!changed && nextActiveTabId === state.activeTabId) return false;

  state.tabs = nextTabs;
  state.activeTabId = nextActiveTabId;
  if (state.workspaceStoreLoaded) scheduleShellWorkspacePersist();
  return true;
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

function datasetPropertyName(attributeName) {
  return String(attributeName || "").replace(/-([a-z])/g, (_match, letter) => letter.toUpperCase());
}

function bindDataAction(container, attributeName, handler, eventName = "click") {
  const datasetKey = datasetPropertyName(attributeName);
  container.querySelectorAll(`[data-${attributeName}]`).forEach((element) => {
    element.addEventListener(eventName, (event) => handler(element.dataset[datasetKey], element, event));
  });
}

function bindOpenExternalAction(container, attributeName) {
  bindDataAction(container, attributeName, (value) => {
    const url = absoluteUrl(value);
    if (url) window.quantlabDesktop.openExternal(url);
  });
}

function bindOpenPathAction(container, attributeName) {
  bindDataAction(container, attributeName, (value) => {
    if (value) window.quantlabDesktop.openPath(value);
  });
}

function bindDataActions(container, actionSpecs) {
  (actionSpecs || []).forEach(([attributeName, handler, eventName = "click"]) => {
    bindDataAction(container, attributeName, handler, eventName);
  });
}

function bindExternalActions(container, attributeNames) {
  (attributeNames || []).forEach((attributeName) => bindOpenExternalAction(container, attributeName));
}

function bindPathActions(container, attributeNames) {
  (attributeNames || []).forEach((attributeName) => bindOpenPathAction(container, attributeName));
}

function renderWorkspaceState() {
  const { status, serverUrl, error, source } = state.workspace;
  const runtimeStatus = deriveRuntimeStatus();
  const {
    localFallbackActive,
    runsIndexed,
    paperSessions,
    brokerSessions,
    stepbitAppReady,
    stepbitCoreReachable,
    stepbitCoreReady,
  } =
    runtimeStatus;
  const runtimeMode = localFallbackActive
    ? "local-only"
    : state.snapshotStatus.status === "error"
      ? "degraded"
      : status === "ready"
        ? "managed"
        : status === "starting"
          ? "booting"
          : "review";
  elements.runtimeSummary.textContent = localFallbackActive
    ? "QuantLab shell running in local-only fallback mode"
    : state.snapshotStatus.status === "error"
    ? "QuantLab runtime degraded"
    : status === "ready"
    ? "QuantLab research surface ready"
    : status === "starting"
    ? "Starting local research surface"
    : status === "stopped"
    ? "Research surface stopped"
    : "Research surface unavailable";
  elements.runtimeMeta.textContent = error
    ? localFallbackActive
      ? `Using outputs/runs/runs_index.json while research_ui is unavailable. Browser-backed Launch/System links stay limited. ${error}`
      : error
    : serverUrl
    ? `${serverUrl}/research_ui/index.html${source === "external" ? " · external server" : " · managed server"}${state.snapshotStatus.status === "error" ? " · API degraded" : ""}`
    : localFallbackActive
    ? "Using outputs/runs/runs_index.json without a live research_ui server. Launch browser surface is transitional and currently unavailable."
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
    createRuntimeChipNode("Mode", runtimeMode, runtimeMode === "managed" ? "up" : runtimeMode === "booting" ? "warn" : runtimeMode === "local-only" ? "warn" : "down"),
    createRuntimeChipNode("QuantLab", status === "ready" ? "up" : status === "starting" ? "starting" : "down", status === "ready" ? "up" : status === "starting" ? "warn" : "down"),
    createRuntimeChipNode("Runs", `${runsIndexed} indexed`, runsIndexed ? "up" : "warn"),
    createRuntimeChipNode("Paper", String(paperSessions), paperSessions ? "up" : "warn"),
    createRuntimeChipNode("Broker", String(brokerSessions), brokerSessions ? "up" : "warn"),
    createRuntimeChipNode(
      "API",
      state.snapshotStatus.source === "local"
        ? "local-only"
        : state.snapshotStatus.status === "error"
        ? "degraded"
        : state.snapshotStatus.lastSuccessAt
        ? "ok"
        : "pending",
      state.snapshotStatus.source === "local"
        ? "warn"
        : state.snapshotStatus.status === "error"
        ? "down"
        : state.snapshotStatus.lastSuccessAt
        ? "up"
        : "warn",
    ),
    createRuntimeChipNode("Stepbit app", stepbitAppReady ? "up" : "down", stepbitAppReady ? "up" : "down"),
    createRuntimeChipNode(
      "Stepbit core",
      stepbitCoreReady ? "ready" : stepbitCoreReachable ? "up" : "down",
      stepbitCoreReady ? "up" : stepbitCoreReachable ? "warn" : "down",
    ),
  );
  syncTopbarChrome();
  renderChatAdapterStatus();
}

function buildRuntimeAlert() {
  if ((state.workspace.status === "error" || state.workspace.status === "stopped") && state.snapshotStatus.source === "local" && getRuns().length) {
    const recentLogs = (state.workspace.logs || []).slice(-4).join("\n");
    return {
      tone: "warn",
      actionLabel: "Retry boot",
      message: `research_ui is unavailable, but the shell is still using the local runs index.${state.workspace.error ? ` ${state.workspace.error}` : ""}${recentLogs ? `\n\nRecent log:\n${recentLogs}` : ""}`,
    };
  }
  if (state.workspace.status === "error" || state.workspace.status === "stopped") {
    const recentLogs = (state.workspace.logs || []).slice(-4).join("\n");
    return {
      tone: "down",
      actionLabel: "Retry boot",
      message: `${state.workspace.status === "error" ? "Boot failed" : "Runtime stopped"}${state.workspace.error ? `: ${state.workspace.error}` : "."}${recentLogs ? `\n\nRecent log:\n${recentLogs}` : ""}`,
    };
  }
  if (state.snapshotStatus.status === "error") {
    const pausedSuffix = state.snapshotStatus.refreshPaused
      ? " Automatic refresh paused after repeated failures."
      : "";
    return {
      tone: "warn",
      actionLabel: "Retry API",
      message: `API unavailable: ${state.snapshotStatus.error || "local request failed."}${pausedSuffix}`,
    };
  }
  if (state.snapshotStatus.status === "degraded" && state.snapshotStatus.source === "local") {
    return {
      tone: "warn",
      actionLabel: state.workspace.serverUrl ? "Retry API" : "Retry boot",
      message: "The shell is running from the local runs index. Browser-backed API surfaces stay limited until research_ui becomes reachable.",
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
    state.snapshotStatus = {
      ...state.snapshotStatus,
      consecutiveErrors: 0,
      refreshPaused: false,
    };
    await refreshSnapshot();
    if (state.workspace.serverUrl && !state.refreshTimer && state.snapshotStatus.status !== "error") {
      ensureRefreshLoop();
    }
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
    syncWorkspaceLayoutMode(null);
    clearElement(elements.tabsBar);
    appendChildren(
      elements.tabContent,
      createElementNode(
        "div",
        {
          className: "tab-placeholder",
          text: SHELL_COPY.emptyWorksurface,
        },
      ),
    );
    elements.topbarTitle.textContent = SHELL_COPY.defaultTopbarTitle;
    syncTopbarChrome();
    syncNav("assistant");
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
  syncWorkspaceLayoutMode(activeTab);
  elements.topbarTitle.textContent = activeTab.title;
  syncTopbarChrome(activeTab);
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
  } else if (activeTab.kind === "runs") {
    renderMarkupInto(elements.tabContent, renderRunsTab(activeTab));
  } else if (activeTab.kind === "run") {
    renderMarkupInto(elements.tabContent, renderRunTab(activeTab));
  } else if (activeTab.kind === "compare") {
    renderMarkupInto(elements.tabContent, renderCompareTab(activeTab));
  } else if (activeTab.kind === "artifacts") {
    renderMarkupInto(elements.tabContent, renderArtifactsTab(activeTab));
  } else if (activeTab.kind === "candidates") {
    renderMarkupInto(elements.tabContent, renderCandidatesTab(activeTab));
  } else if (activeTab.kind === "paper") {
    renderMarkupInto(elements.tabContent, renderPaperOpsTab());
  } else if (activeTab.kind === "system") {
    renderMarkupInto(elements.tabContent, renderSystemTab());
  } else if (activeTab.kind === "job") {
    renderMarkupInto(elements.tabContent, renderJobTab(activeTab));
  } else {
    appendChildren(elements.tabContent, createElementNode("div", { className: "tab-placeholder", text: activeTab.content || "" }));
  }
  bindTabChromeEvents();
  bindTabContentEvents(activeTab);
}

function syncWorkspaceLayoutMode(activeTab) {
  if (!elements.workspaceGrid) return;
  const kind = activeTab?.kind || "";
  const priority = WORKBENCH_PRIORITY_KINDS.has(kind) ? "high" : "normal";
  elements.workspaceGrid.dataset.activeTabKind = kind;
  elements.workspaceGrid.dataset.workbenchPriority = priority;
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
    appendChildren(elements.paletteResults, createEmptyStateNode(SHELL_COPY.paletteEmptyState));
  } else {
    appendChildren(
      elements.paletteResults,
      visibleActions.map((action) =>
        createElementNode(
          "button",
          {
            className: "palette-item",
            dataset: { paletteAction: action.id },
            type: "button",
          },
          [
            createElementNode("strong", { className: "palette-label", text: action.label }),
            createElementNode("span", { text: action.description }),
          ],
        ),
      ),
    );
  }
  elements.paletteResults.querySelectorAll("[data-palette-action]").forEach((button) => {
    const paletteButton = /** @type {HTMLElement} */ (button);
    paletteButton.addEventListener("click", () => {
      const action = paletteActions.find((entry) => entry.id === paletteButton.dataset.paletteAction);
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
  bindDataAction(elements.workflowJobsList, "open-job", (value) => openJobTab(value));
  bindDataAction(elements.workflowJobsList, "open-run", (value) => openRunDetailTab(value));
  bindDataAction(elements.workflowJobsList, "open-job-artifacts", (value) => openArtifactsForJob(value));
}

function setTopbarChip(element, text, tone = "muted") {
  if (!element) return;
  element.textContent = text;
  element.className = `topbar-status-chip ${tone}`.trim();
}

function summarizeServerChip() {
  const { status, serverUrl, source } = state.workspace;
  if (!serverUrl && state.snapshotStatus.source === "local") {
    return {
      text: "Local fallback",
      tone: "warn",
    };
  }
  if (!serverUrl) {
    return {
      text: status === "starting" ? "Bootstrap booting" : SHELL_COPY.defaultTopbarServer,
      tone: status === "error" || status === "stopped" ? "down" : "muted",
    };
  }
  const label = serverUrl.replace(/^https?:\/\//i, "");
  return {
    text: `${source === "external" ? "External" : "Managed"} · ${label}`,
    tone: source === "external" ? "warn" : "muted",
  };
}

function summarizeRuntimeChip() {
  const runtimeStatus = deriveRuntimeStatus();
  if (runtimeStatus.localFallbackActive) {
    return { text: "Runtime fallback", tone: "warn" };
  }
  if (state.snapshotStatus.status === "error") {
    return { text: "Runtime degraded", tone: "down" };
  }
  if (runtimeStatus.workspaceStatus === "ready") {
    return { text: "Runtime live", tone: "up" };
  }
  if (runtimeStatus.workspaceStatus === "starting") {
    return { text: "Runtime booting", tone: "warn" };
  }
  if (runtimeStatus.workspaceStatus === "error" || runtimeStatus.workspaceStatus === "stopped") {
    return { text: "Runtime review", tone: "down" };
  }
  return { text: SHELL_COPY.defaultTopbarRuntime, tone: "muted" };
}

function summarizeSurfaceChip(activeTab) {
  if (!activeTab) return { text: SHELL_COPY.defaultTopbarSurface, tone: "muted" };
  const navKind = activeTab.navKind || activeTab.kind || "surface";
  return {
    text: `${titleCase(navKind)} surface`,
    tone: "muted",
  };
}

function syncTopbarChrome(activeTab = state.tabs.find((tab) => tab.id === state.activeTabId) || null) {
  if (elements.topbarEyebrow) {
    elements.topbarEyebrow.textContent = SHELL_COPY.topbarEyebrow;
  }
  const runtimeChip = summarizeRuntimeChip();
  const serverChip = summarizeServerChip();
  const surfaceChip = summarizeSurfaceChip(activeTab);
  setTopbarChip(elements.topbarRuntimeChip, runtimeChip.text, runtimeChip.tone);
  setTopbarChip(elements.topbarServerChip, serverChip.text, serverChip.tone);
  setTopbarChip(elements.topbarSurfaceChip, surfaceChip.text, surfaceChip.tone);
}

function renderRunsWorklist(runs) {
  if (!runs.length) {
    appendChildren(elements.workflowRunsList, createEmptyStateNode("The run index is still empty. Launch a run or wait for artifacts to appear."));
    return;
  }
  appendChildren(elements.workflowRunsList, runs.map((run) => createRunWorklistNode(run)));
  bindDataAction(elements.workflowRunsList, "select-run", (value, input) => toggleRunSelection(value, input.checked), "change");
  bindDataAction(elements.workflowRunsList, "open-run", (value) => openRunDetailTab(value));
  bindDataAction(elements.workflowRunsList, "toggle-candidate", (value) => toggleCandidate(value));
  bindDataAction(elements.workflowRunsList, "open-artifacts", (value) => openArtifactsTabForRun(value));
}

function bindTabChromeEvents() {
  elements.tabsBar.querySelectorAll("[data-tab-id]").forEach((button) => {
    const tabButton = /** @type {HTMLElement} */ (button);
    tabButton.addEventListener("click", () => {
      state.activeTabId = tabButton.dataset.tabId;
      renderTabs();
      scheduleShellWorkspacePersist();
    });
  });
  elements.tabsBar.querySelectorAll("[data-close-tab]").forEach((button) => {
    const closeButton = /** @type {HTMLElement} */ (button);
    closeButton.addEventListener("click", (event) => {
      event.stopPropagation();
      closeTab(closeButton.dataset.closeTab);
    });
  });
}

const TAB_CONTENT_EVENT_BINDERS = {
  experiments(tab) {
    bindDataActions(elements.tabContent, [
      ["experiments-refresh", () => refreshExperimentsWorkspace({ focusTab: true, silent: false })],
      ["experiment-config", (value) => upsertTab({ id: tab.id, selectedConfigPath: value })],
      ["experiment-launch-config", async (configPath) => {
        if (!configPath) return;
        await submitLaunchRequest({ command: "sweep", params: { config_path: configPath } }, "experiments");
        await refreshExperimentsWorkspace({ focusTab: true, silent: true });
        upsertTab({ id: tab.id, selectedConfigPath: configPath });
      }],
      ["experiment-sweep", (value) => upsertTab({ id: tab.id, selectedSweepId: value })],
      ["experiment-relaunch", async (configPath) => {
        if (!configPath) return;
        await submitLaunchRequest({ command: "sweep", params: { config_path: configPath } }, "experiments");
        await refreshExperimentsWorkspace({ focusTab: true, silent: true });
      }],
      ["sweep-track-entry", (value) => {
        const row = findSweepDecisionRow(value);
        if (row) toggleSweepDecisionEntry(row);
      }],
      ["sweep-shortlist-entry", (value) => toggleSweepDecisionShortlist(value)],
      ["sweep-baseline-entry", (value) => setSweepDecisionBaseline(value)],
      ["sweep-note-entry", (value) => editSweepDecisionNote(value)],
      ["open-sweep-handoff", (value) => openSweepDecisionTab(value || "tracked")],
    ]);
    bindPathActions(elements.tabContent, ["experiment-open-path", "experiment-open-file", "open-path"]);
  },

  run(tab) {
    bindRunContextActions(elements.tabContent, tab.runId);
  },

  runs() {
    bindDataActions(elements.tabContent, [
      ["open-run", (value) => openRunDetailTab(value)],
      ["open-artifacts", (value) => openArtifactsTabForRun(value)],
      ["mark-candidate", (value) => toggleCandidate(value)],
      ["open-job", (value) => openJobTab(value)],
      ["open-candidates", () => openCandidatesTab()],
      ["open-ops", () => openPaperOpsTab()],
      ["open-shortlist-compare", () => openShortlistCompareTab()],
      ["open-system-tab", () => openSystemTab()],
    ]);
  },

  compare(tab) {
    bindDataActions(elements.tabContent, [
      ["open-run", (value) => openRunDetailTab(value)],
      ["open-artifacts", (value) => openArtifactsTabForRun(value)],
      ["compare-rank", (value) => upsertTab({ id: tab.id, rankMetric: value })],
      ["mark-candidate", (value) => toggleCandidate(value)],
      ["shortlist-run", (value) => toggleShortlist(value)],
      ["set-baseline", (value) => setBaseline(value)],
    ]);
  },

  artifacts(tab) {
    bindExternalActions(elements.tabContent, ["open-external"]);
    bindPathActions(elements.tabContent, ["open-path"]);
    bindDataActions(elements.tabContent, [["open-run", (value) => openRunDetailTab(value)]]);
    bindRunContextActions(elements.tabContent, tab.runId);
  },

  candidates(tab) {
    bindDataActions(elements.tabContent, [
      ["candidates-filter", (value) => upsertTab({ id: tab.id, filter: value })],
      ["open-run", (value) => openRunDetailTab(value)],
      ["open-artifacts", (value) => openArtifactsTabForRun(value)],
      ["mark-candidate", (value) => toggleCandidate(value)],
      ["shortlist-run", (value) => toggleShortlist(value)],
      ["set-baseline", (value) => setBaseline(value)],
      ["edit-note", (value) => editCandidateNote(value)],
      ["open-shortlist-compare", () => openShortlistCompareTab()],
    ]);
  },

  paper() {
    bindDataActions(elements.tabContent, [
      ["open-job", (value) => openJobTab(value)],
      ["open-run", (value) => openRunDetailTab(value)],
      ["open-artifacts", (value) => openArtifactsTabForRun(value)],
      ["open-shortlist-compare", () => openShortlistCompareTab()],
    ]);
    bindExternalActions(elements.tabContent, ["open-browser-ops"]);
  },

  system() {
    bindDataActions(elements.tabContent, [
      ["system-retry", () => retryWorkspaceRuntime()],
      ["open-job", (value) => openJobTab(value)],
      ["open-run", (value) => openRunDetailTab(value)],
    ]);
    bindExternalActions(elements.tabContent, ["open-system-url"]);
  },

  job() {
    bindDataActions(elements.tabContent, [
      ["open-run", (value) => openRunDetailTab(value)],
      ["open-job-artifacts", (value) => openArtifactsForJob(value)],
    ]);
    bindExternalActions(elements.tabContent, ["open-job-link"]);
  },

  "sweep-decision"(tab) {
    bindDataActions(elements.tabContent, [
      ["sweep-rank", (value) => upsertTab({ id: tab.id, rankMetric: value })],
      ["sweep-track-entry", (value) => {
        const row = findSweepDecisionRow(value) || getSweepDecisionResolvedEntry(value)?.row;
        if (row) toggleSweepDecisionEntry(row);
      }],
      ["sweep-shortlist-entry", (value) => toggleSweepDecisionShortlist(value)],
      ["sweep-baseline-entry", (value) => setSweepDecisionBaseline(value)],
      ["sweep-note-entry", (value) => editSweepDecisionNote(value)],
      ["experiment-launch-config", async (configPath) => {
        if (!configPath) return;
        await submitLaunchRequest({ command: "sweep", params: { config_path: configPath } }, "sweep-handoff");
        await refreshExperimentsWorkspace({ focusTab: false, silent: true });
      }],
    ]);
    bindPathActions(elements.tabContent, ["experiment-open-path"]);
  },
};

function bindTabContentEvents(tab) {
  TAB_CONTENT_EVENT_BINDERS[tab.kind]?.(tab);
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
  if (normalized.includes("open system") || normalized.includes("open runtime") || normalized === "system") {
    openSystemTab();
    pushMessage("assistant", "Opened the runtime diagnostics surface.");
    return;
  }
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
    openExperimentsTab();
    pushMessage("assistant", "Opened the Experiments workspace (Launch is now integrated into this surface).");
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
    openRunsNativeTab();
    pushMessage("assistant", "Opened the native run explorer.");
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
  pushMessage("assistant", SHELL_COPY.assistantHelp);
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
  const runtimeStatus = deriveRuntimeStatus();
  const stepbit = state.snapshot?.stepbitWorkspace?.live_urls || {};
  const runtimeMode = runtimeStatus.localFallbackActive
    ? "local-only fallback"
    : state.snapshotStatus.status === "error"
      ? "degraded"
      : runtimeStatus.workspaceStatus === "ready"
        ? "managed live"
        : runtimeStatus.workspaceStatus === "starting"
          ? "booting"
          : "review required";
  pushMessage("assistant", [
    `Runtime mode: ${runtimeMode}`,
    `QuantLab server: ${runtimeStatus.workspaceStatus}`,
    `Server URL: ${runtimeStatus.serverUrl || "pending"}`,
    `Snapshot source: ${state.snapshotStatus.source || "none"}`,
    `Indexed runs: ${runtimeStatus.runsIndexed}`,
    `Selected runs: ${state.selectedRunIds.length}`,
    `Candidates: ${getCandidateEntries().length}`,
    `Shortlisted: ${getShortlistRunIds().length}`,
    `Baseline: ${state.candidatesStore.baseline_run_id || "none"}`,
    `Stepbit frontend: ${stepbit.frontend_reachable ? "up" : "down"}`,
    `Stepbit backend: ${stepbit.backend_reachable ? "up" : "down"}`,
    `Stepbit core: ${stepbit.core_ready ? "ready" : stepbit.core_reachable ? "up" : "down"}`,
  ].join("\n"));
}

/**
 * @returns {RuntimeStatus}
 */
function deriveRuntimeStatus() {
  const runs = getRuns();
  const stepbit = state.snapshot?.stepbitWorkspace?.live_urls || {};
  return {
    workspaceStatus: state.workspace.status,
    workspaceSource: state.workspace.source,
    serverUrl: state.workspace.serverUrl,
    localFallbackActive: state.snapshotStatus.source === "local" && runs.length > 0,
    runsIndexed: runs.length,
    paperSessions: state.snapshot?.paperHealth?.total_sessions || 0,
    brokerSessions: state.snapshot?.brokerHealth?.total_sessions || 0,
    stepbitAppReady: Boolean(stepbit.frontend_reachable),
    stepbitCoreReachable: Boolean(stepbit.core_reachable),
    stepbitCoreReady: Boolean(stepbit.core_ready),
  };
}

function focusAssistant() {
  elements.chatInput.focus();
  elements.chatInput.scrollIntoView({ block: "nearest" });
}

function openSystemTab() {
  upsertTab({
    id: "system",
    kind: "system",
    navKind: "system",
    title: "System",
  });
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

function openRunsNativeTab() {
  upsertTab({
    id: "runs-native",
    kind: "runs",
    navKind: "runs",
    title: "Runs",
  });
}

function maybeOpenDefaultSurface() {
  if (state.initialSurfaceResolved) return;
  if (state.tabs.length) {
    state.initialSurfaceResolved = true;
    return;
  }
  state.initialSurfaceResolved = true;
  openRunsNativeTab();
}

function openResearchTab(navKind, title, hash) {
  if (!state.workspace.serverUrl) {
    const runtimeStatus = deriveRuntimeStatus();
    if (runtimeStatus.localFallbackActive) {
      pushMessage("assistant", "This browser-backed surface is unavailable because research_ui is offline. The workstation remains usable in local-only mode; use native Runs/Paper Ops/System until runtime recovers.");
      return;
    }
    if (state.workspace.status === "error" || state.workspace.status === "stopped") {
      pushMessage("assistant", "research_ui is unavailable right now. Open System and use Retry runtime; the rest of the workstation can still run from local artifacts when available.");
      return;
    }
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
        selectedConfigPath: resolveExperimentConfigPath(experimentsTab.selectedConfigPath, workspace.configs),
        selectedSweepId: resolveExperimentSweepId(experimentsTab.selectedSweepId, workspace.sweeps),
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
    reconcileWorkspaceTabs();
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
  const files = fileListing.entries || [];
  const hasFile = (fileName) => files.some((file) => file.name === fileName);
  const metaPath = `${rootPath}\\meta.json`;
  const leaderboardPath = `${rootPath}\\leaderboard.csv`;
  const experimentsPath = `${rootPath}\\experiments.csv`;
  const walkforwardSummaryPath = `${rootPath}\\walkforward_summary.csv`;
  const configResolvedPath = `${rootPath}\\config_resolved.yaml`;

  const [meta, leaderboardText, experimentsText, walkforwardText] = await Promise.all([
    hasFile("meta.json") ? readOptionalProjectJson(metaPath) : Promise.resolve(null),
    hasFile("leaderboard.csv") ? readOptionalProjectText(leaderboardPath) : Promise.resolve(""),
    hasFile("experiments.csv") ? readOptionalProjectText(experimentsPath) : Promise.resolve(""),
    hasFile("walkforward_summary.csv") ? readOptionalProjectText(walkforwardSummaryPath) : Promise.resolve(""),
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
  const hasStructuredData = Boolean(
    leaderboardRows.length
    || walkforwardRows.length
    || experimentsRows.length
    || decisionRows.length
    || (Array.isArray(meta?.top10) && meta.top10.length),
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
    files,
    filesTruncated: Boolean(fileListing.truncated),
    metaPath,
    leaderboardPath,
    experimentsPath,
    walkforwardSummaryPath,
    configResolvedPath,
    hasStructuredData,
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
  const target = document.querySelector(`.nav-item[data-action="${NAV_ACTION_BY_KIND[kind] || NAV_ACTION_BY_KIND.assistant}"]`);
  if (target) target.classList.add("is-active");
}

function buildPaletteActionHandler(handlerName) {
  const handlers = {
    askStepbitAboutLatestFailure,
    explainLatestFailureInChat,
    focusAssistant,
    openArtifactsForPreferredRun,
    openBaselineRunTab,
    openCandidatesTab,
    openCompareSelectionTab,
    openExperimentsTab,
    openLatestFailedLaunchTab,
    openLatestRunTab,
    openPaperOpsTab,
    openRunsNativeTab,
    openShortlistCompareTab,
    openSweepDecisionTab,
    openSystemTab,
    summarizeRuntimeInChat,
  };
  return handlers[handlerName] || (() => {});
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

function renderRunsTab(tab) {
  return renderRunsTabView(tab, getRendererContext());
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

function renderSystemTab() {
  return renderSystemTabView(getRendererContext());
}

function renderJobTab(tab) {
  return renderJobTabView(tab, getRendererContext());
}

function getRendererContext() {
  return {
    store: state.candidatesStore,
    snapshot: state.snapshot,
    workspace: state.workspace,
    snapshotStatus: state.snapshotStatus,
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
    selectedRunIds: state.selectedRunIds,
    getSelectedRuns,
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
  if (index >= 0) {
    state.tabs[index] = { ...state.tabs[index], ...nextTab };
  } else {
    state.tabs.push(nextTab);
    if (state.tabs.length > CONFIG.maxSurfaceTabs) {
      // Find oldest tab that isn't the one we just added (or active)
      const evictIndex = state.tabs.findIndex((tab) => tab.id !== nextTab.id && tab.id !== state.activeTabId);
      if (evictIndex >= 0) {
        state.tabs.splice(evictIndex, 1);
      }
    }
  }
  state.activeTabId = nextTab.id;
  renderTabs();
  scheduleShellWorkspacePersist();
}

function rerenderContextualTabs() {
  if (state.tabs.some((tab) => ["system", "experiments", "sweep-decision", "run", "runs", "compare", "artifacts", "candidates", "paper", "job"].includes(tab.kind))) renderTabs();
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
    const localArtifactPath = joinProjectPath(run.path, artifact);
    const href = buildRunArtifactHref(run.path, artifact);
    try {
      const report = await window.quantlabDesktop.readProjectJson(localArtifactPath);
      detail = { ...detail, report, reportUrl: href || localArtifactPath };
      break;
    } catch (_localError) {
      if (!href) continue;
      try {
        const report = await window.quantlabDesktop.requestJson(href);
        detail = { ...detail, report, reportUrl: href };
        break;
      } catch (_error) {
        // Keep trying the remaining artifact names.
      }
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
  if (activeTab?.kind === "system") return `${state.workspace.serverUrl}/research_ui/index.html`;
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
  bindDataAction(container, "open-artifacts", (value) => openArtifactsTabForRun(value || runId));
  bindDataAction(container, "mark-candidate", (value) => toggleCandidate(value));
  bindDataAction(container, "shortlist-run", (value) => toggleShortlist(value));
  bindDataAction(container, "set-baseline", (value) => setBaseline(value));
  bindDataAction(container, "edit-note", (value) => editCandidateNote(value));
  bindDataAction(container, "open-browser-run", (value) => {
    const url = getBrowserUrlForRun(value || runId);
    if (url) window.quantlabDesktop.openExternal(url);
  });
  bindDataAction(container, "open-decision-compare", (value) => openRunDecisionCompare(value || runId));
  bindDataAction(container, "open-related-job", (value) => openLatestRelatedLaunchJobForRun(value || runId));
  bindDataAction(container, "open-sweep-handoff", (value) => openSweepDecisionTab(value || "tracked"));
  bindDataAction(container, "open-candidates", () => openCandidatesTab());
  bindOpenExternalAction(container, "open-job-link");
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
    if (state.workspace.serverUrl) {
      return await window.quantlabDesktop.requestText(relativePath);
    }
  } catch (_error) {
    // Fall through to local file access.
  }
  const projectPath = projectPathFromHref(relativePath);
  if (!projectPath) return "";
  try {
    return await window.quantlabDesktop.readProjectText(projectPath);
  } catch (_error) {
    return "";
  }
}

function joinProjectPath(basePath, leafName) {
  return `${String(basePath || "").replace(/[\\/]+$/, "")}/${leafName}`;
}

function projectPathFromHref(relativeOrUrl) {
  const raw = String(relativeOrUrl || "").trim();
  if (!raw) return "";
  if (/^https?:\/\//i.test(raw)) {
    try {
      return projectPathFromHref(new URL(raw).pathname);
    } catch (_error) {
      return "";
    }
  }
  const normalized = raw.replace(/^\/+/, "");
  if (!normalized || normalized.startsWith("api/")) return "";
  return normalized;
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
