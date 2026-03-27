const state = {
  workspace: {
    status: "starting",
    serverUrl: null,
    logs: [],
    error: null,
  },
  snapshot: null,
  chatMessages: [
    {
      role: "assistant",
      content:
        "QuantLab Desktop v0 is ready as a command bus.\n\nTry commands like:\n- open launch\n- open runs\n- open compare\n- open ops\n- open latest run\n- show runtime status\n\nThis shell is specialized for QuantLab and keeps the product centered on one workspace.",
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
};

const paletteActions = [
  { id: "chat", label: "Open Chat", description: "Return focus to the QuantLab command bus.", run: () => focusChat() },
  { id: "launch", label: "Open Launch", description: "Open the QuantLab launch surface.", run: () => openResearchTab("launch", "Launch", "#/launch") },
  { id: "runs", label: "Open Runs", description: "Open the run explorer.", run: () => openResearchTab("runs", "Runs", "#/") },
  { id: "compare", label: "Open Compare", description: "Open the comparison surface.", run: () => openResearchTab("compare", "Compare", "#/compare") },
  { id: "ops", label: "Open Paper Ops", description: "Open runtime and operational surfaces.", run: () => openResearchTab("ops", "Paper Ops", "#/ops") },
  { id: "latest-run", label: "Open Latest Run", description: "Open the latest indexed run detail.", run: () => openLatestRunTab() },
  { id: "runtime", label: "Show Runtime Status", description: "Summarize local service health in chat.", run: () => summarizeRuntimeInChat() },
];

document.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  renderAll();

  const initialState = await window.quantlabDesktop.getWorkspaceState();
  state.workspace = initialState;
  renderWorkspaceState();

  window.quantlabDesktop.onWorkspaceState((payload) => {
    state.workspace = payload;
    renderWorkspaceState();
    if (payload.serverUrl) {
      refreshSnapshot();
    }
  });

  if (initialState.serverUrl) {
    refreshSnapshot();
  }
});

function bindEvents() {
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.action;
      if (action === "open-chat") focusChat();
      if (action === "open-launch") openResearchTab("launch", "Launch", "#/launch");
      if (action === "open-runs") openResearchTab("runs", "Runs", "#/");
      if (action === "open-compare") openResearchTab("compare", "Compare", "#/compare");
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
    if (!state.workspace.serverUrl) return;
    window.quantlabDesktop.openExternal(`${state.workspace.serverUrl}/research_ui/index.html#/`);
  });
}

async function refreshSnapshot() {
  if (!state.workspace.serverUrl) return;
  try {
    const [runsRegistry, launchControl, paperHealth, brokerHealth, stepbitWorkspace] = await Promise.all([
      window.quantlabDesktop.requestJson("/outputs/runs/runs_index.json"),
      window.quantlabDesktop.requestJson("/api/launch-control"),
      window.quantlabDesktop.requestJson("/api/paper-sessions-health"),
      window.quantlabDesktop.requestJson("/api/broker-submissions-health"),
      window.quantlabDesktop.requestJson("/api/stepbit-workspace"),
    ]);
    state.snapshot = { runsRegistry, launchControl, paperHealth, brokerHealth, stepbitWorkspace };
    renderWorkspaceState();
  } catch (_error) {
    // Best effort snapshot refresh.
  }
}

function renderAll() {
  renderChat();
  renderTabs();
  renderPalette();
}

function renderWorkspaceState() {
  const { status, serverUrl, error } = state.workspace;
  const runs = state.snapshot?.runsRegistry?.runs || [];
  const stepbit = state.snapshot?.stepbitWorkspace?.live_urls || {};
  const paperCount = state.snapshot?.paperHealth?.total_sessions || 0;
  const brokerCount = state.snapshot?.brokerHealth?.total_sessions || 0;

  elements.runtimeSummary.textContent =
    status === "ready"
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
  elements.chatLog.innerHTML = state.chatMessages
    .map(
      (message) => `
        <article class="message ${message.role}">
          <div class="message-role">${escapeHtml(message.role)}</div>
          <div class="message-body">${escapeHtml(message.content)}</div>
        </article>
      `
    )
    .join("");
}

function renderTabs() {
  if (!state.tabs.length) {
    elements.tabsBar.innerHTML = "";
    elements.tabContent.innerHTML = `
      <div class="tab-placeholder">
        No context tab is open yet.

        Use chat, quick command, or the palette to open Launch, Runs, Compare, or Paper Ops.
      </div>
    `;
    elements.topbarTitle.textContent = "Chat";
    syncNav("chat");
    return;
  }

  elements.tabsBar.innerHTML = state.tabs
    .map(
      (tab) => `
        <button class="tab-pill ${tab.id === state.activeTabId ? "is-active" : ""}" data-tab-id="${escapeHtml(tab.id)}" type="button">
          <span>${escapeHtml(tab.title)}</span>
          <span class="tab-close" data-close-tab="${escapeHtml(tab.id)}">×</span>
        </button>
      `
    )
    .join("");

  const activeTab = state.tabs.find((tab) => tab.id === state.activeTabId) || state.tabs[0];
  state.activeTabId = activeTab.id;
  elements.topbarTitle.textContent = activeTab.title;
  syncNav(activeTab.kind);

  elements.tabContent.innerHTML = activeTab.kind === "placeholder"
    ? `<div class="tab-placeholder">${escapeHtml(activeTab.content)}</div>`
    : `<iframe class="tab-frame" src="${escapeHtml(activeTab.url)}" title="${escapeHtml(activeTab.title)}"></iframe>`;

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

function renderPalette() {
  elements.paletteOverlay.classList.toggle("hidden", !state.paletteOpen);
  if (!state.paletteOpen) return;

  elements.paletteResults.innerHTML = paletteActions
    .map(
      (action) => `
        <button class="palette-item" data-palette-action="${escapeHtml(action.id)}" type="button">
          <strong>${escapeHtml(action.label)}</strong>
          <span>${escapeHtml(action.description)}</span>
        </button>
      `
    )
    .join("");

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

function handleChatPrompt(prompt) {
  pushMessage("user", prompt);
  const normalized = prompt.trim().toLowerCase();

  if (normalized.includes("open launch") || normalized === "launch") {
    openResearchTab("launch", "Launch", "#/launch");
    pushMessage("assistant", "Opened the Launch surface inside a desktop tab.");
    return;
  }
  if (normalized.includes("open compare") || normalized.includes("compare")) {
    openResearchTab("compare", "Compare", "#/compare");
    pushMessage("assistant", "Opened the Compare surface.");
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
  if (normalized.includes("show runtime status") || normalized === "status") {
    summarizeRuntimeInChat();
    return;
  }

  pushMessage(
    "assistant",
    "This first desktop block is deterministic rather than fully AI-driven. Try:\n- open launch\n- open runs\n- open compare\n- open ops\n- open latest run\n- show runtime status"
  );
}

function summarizeRuntimeInChat() {
  const runs = state.snapshot?.runsRegistry?.runs || [];
  const stepbit = state.snapshot?.stepbitWorkspace?.live_urls || {};
  pushMessage(
    "assistant",
    [
      `QuantLab server: ${state.workspace.status}`,
      `Server URL: ${state.workspace.serverUrl || "pending"}`,
      `Indexed runs: ${runs.length}`,
      `Stepbit frontend: ${stepbit.frontend_reachable ? "up" : "down"}`,
      `Stepbit backend: ${stepbit.backend_reachable ? "up" : "down"}`,
      `Stepbit core: ${stepbit.core_ready ? "ready" : stepbit.core_reachable ? "up" : "down"}`,
    ].join("\n")
  );
}

function focusChat() {
  state.activeTabId = null;
  renderTabs();
  pushMessage("assistant", "Chat is the center of the workspace. Use it to open surfaces or ask for deterministic actions.");
}

function openResearchTab(kind, title, hash) {
  if (!state.workspace.serverUrl) {
    pushMessage("assistant", "The local research surface is still starting. Wait a moment and retry.");
    return;
  }
  const id = `${kind}:${hash}`;
  const existing = state.tabs.find((tab) => tab.id === id);
  if (existing) {
    state.activeTabId = existing.id;
    renderTabs();
    return;
  }
  state.tabs.push({
    id,
    kind,
    title,
    url: `${state.workspace.serverUrl}/research_ui/index.html${hash}`,
  });
  state.activeTabId = id;
  renderTabs();
}

function openLatestRunTab() {
  const latestRun = state.snapshot?.runsRegistry?.runs?.[0];
  if (!latestRun || !latestRun.run_id) {
    pushMessage("assistant", "No indexed runs are available yet, so there is no latest run to open.");
    return;
  }
  openResearchTab("runs", `Run ${latestRun.run_id}`, `#/run/${encodeURIComponent(latestRun.run_id)}`);
  pushMessage("assistant", `Opened the latest indexed run: ${latestRun.run_id}.`);
}

function closeTab(tabId) {
  state.tabs = state.tabs.filter((tab) => tab.id !== tabId);
  if (state.activeTabId === tabId) {
    state.activeTabId = state.tabs[0]?.id || null;
  }
  renderTabs();
}

function syncNav(kind) {
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("is-active"));
  const mapping = {
    chat: "open-chat",
    launch: "open-launch",
    runs: "open-runs",
    compare: "open-compare",
    ops: "open-ops",
  };
  const target = document.querySelector(`.nav-item[data-action="${mapping[kind] || "open-chat"}"]`);
  if (target) target.classList.add("is-active");
}

function pushMessage(role, content) {
  state.chatMessages.push({ role, content });
  renderChat();
}

function runtimeChip(label, value, tone) {
  return `
    <div class="runtime-chip ${escapeHtml(tone)}">
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(value)}</span>
    </div>
  `;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
