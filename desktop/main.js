const { app, BrowserWindow, ipcMain, shell } = require("electron");
const fs = require("fs");
const fsp = require("fs/promises");
const path = require("path");
const { spawn } = require("child_process");

const DESKTOP_ROOT = __dirname;
const PROJECT_ROOT = path.resolve(DESKTOP_ROOT, "..");
const WORKSPACE_ROOT = path.resolve(PROJECT_ROOT, "..");
const SERVER_SCRIPT = path.join(PROJECT_ROOT, "research_ui", "server.py");
const OUTPUTS_ROOT = process.env.QUANTLAB_DESKTOP_OUTPUTS_ROOT
  ? path.resolve(process.env.QUANTLAB_DESKTOP_OUTPUTS_ROOT)
  : path.join(PROJECT_ROOT, "outputs");
const DESKTOP_OUTPUTS_ROOT = path.join(OUTPUTS_ROOT, "desktop");
const CANDIDATES_STORE_PATH = path.join(DESKTOP_OUTPUTS_ROOT, "candidates_shortlist.json");
const SWEEP_DECISION_STORE_PATH = path.join(DESKTOP_OUTPUTS_ROOT, "sweep_decision_handoff.json");
const WORKSPACE_STORE_PATH = path.join(DESKTOP_OUTPUTS_ROOT, "workspace_state.json");
const STEPBIT_APP_ROOT = path.join(WORKSPACE_ROOT, "stepbit-app");
const STEPBIT_APP_CONFIG_PATH = path.join(STEPBIT_APP_ROOT, "config.yaml");
const MAX_DIRECTORY_ENTRIES = 240;
const RESEARCH_UI_URLS = [
  "http://127.0.0.1:8000",
  "http://localhost:8000",
];
const RESEARCH_UI_HEALTH_PATH = "/api/paper-sessions-health";
const RESEARCH_UI_STARTUP_TIMEOUT_MS = 25000;
const ELECTRON_STATE_ROOT = path.join(DESKTOP_OUTPUTS_ROOT, "electron");
const IS_SMOKE_RUN = process.env.QUANTLAB_DESKTOP_SMOKE === "1";
const SMOKE_OUTPUT_PATH = process.env.QUANTLAB_DESKTOP_SMOKE_OUTPUT || "";

app.setPath("userData", path.join(ELECTRON_STATE_ROOT, "user-data"));
app.setPath("cache", path.join(ELECTRON_STATE_ROOT, "cache"));

const singleInstanceLock = app.requestSingleInstanceLock();
if (!singleInstanceLock) {
  app.quit();
  process.exit(0);
}

let mainWindow = null;
let researchServerProcess = null;
let researchServerOwned = false;
let researchStartupTimer = null;
let workspaceState = {
  status: "idle",
  serverUrl: null,
  logs: [],
  error: null,
  source: null,
};

function defaultCandidatesStore() {
  return {
    version: 1,
    updated_at: null,
    baseline_run_id: null,
    entries: [],
  };
}

function normalizeCandidateEntry(entry) {
  if (!entry || typeof entry !== "object" || !entry.run_id) return null;
  const now = new Date().toISOString();
  return {
    run_id: String(entry.run_id),
    note: typeof entry.note === "string" ? entry.note : "",
    shortlisted: Boolean(entry.shortlisted),
    created_at: entry.created_at || now,
    updated_at: entry.updated_at || now,
  };
}

function normalizeCandidatesStore(store) {
  const fallback = defaultCandidatesStore();
  if (!store || typeof store !== "object") return fallback;
  const entries = Array.isArray(store.entries)
    ? store.entries.map(normalizeCandidateEntry).filter(Boolean)
    : [];
  return {
    version: 1,
    updated_at: store.updated_at || null,
    baseline_run_id: store.baseline_run_id ? String(store.baseline_run_id) : null,
    entries,
  };
}

function assertPathInsideProject(targetPath) {
  const resolvedProjectRoot = path.resolve(PROJECT_ROOT);
  const rawTarget = String(targetPath || "").trim();
  const resolvedTarget = path.isAbsolute(rawTarget)
    ? path.resolve(rawTarget)
    : path.resolve(PROJECT_ROOT, rawTarget);
  const relative = path.relative(resolvedProjectRoot, resolvedTarget);
  if (!resolvedTarget || relative.startsWith("..") || path.isAbsolute(relative) && relative === resolvedTarget) {
    throw new Error("Requested path is outside the QuantLab workspace.");
  }
  return resolvedTarget;
}

async function readCandidatesStore() {
  try {
    const raw = await fsp.readFile(CANDIDATES_STORE_PATH, "utf8");
    return normalizeCandidatesStore(JSON.parse(raw));
  } catch (error) {
    if (error && error.code === "ENOENT") return defaultCandidatesStore();
    throw error;
  }
}

async function writeCandidatesStore(store) {
  const normalized = normalizeCandidatesStore(store);
  normalized.updated_at = new Date().toISOString();
  await fsp.mkdir(path.dirname(CANDIDATES_STORE_PATH), { recursive: true });
  await fsp.writeFile(CANDIDATES_STORE_PATH, `${JSON.stringify(normalized, null, 2)}\n`, "utf8");
  return normalized;
}

function defaultSweepDecisionStore() {
  return {
    version: 1,
    updated_at: null,
    baseline_entry_id: null,
    entries: [],
  };
}

function normalizeSweepDecisionEntry(entry) {
  if (!entry || typeof entry !== "object" || !entry.entry_id || !entry.sweep_run_id) return null;
  const now = new Date().toISOString();
  return {
    entry_id: String(entry.entry_id),
    sweep_run_id: String(entry.sweep_run_id),
    source: typeof entry.source === "string" ? entry.source : "leaderboard",
    row_index: Number.isFinite(Number(entry.row_index)) ? Number(entry.row_index) : 0,
    note: typeof entry.note === "string" ? entry.note : "",
    shortlisted: Boolean(entry.shortlisted),
    config_path: typeof entry.config_path === "string" ? entry.config_path : "",
    row_snapshot: entry.row_snapshot && typeof entry.row_snapshot === "object" ? entry.row_snapshot : null,
    created_at: entry.created_at || now,
    updated_at: entry.updated_at || now,
  };
}

function normalizeSweepDecisionStore(store) {
  const fallback = defaultSweepDecisionStore();
  if (!store || typeof store !== "object") return fallback;
  const entries = Array.isArray(store.entries)
    ? store.entries.map(normalizeSweepDecisionEntry).filter(Boolean)
    : [];
  return {
    version: 1,
    updated_at: store.updated_at || null,
    baseline_entry_id: store.baseline_entry_id ? String(store.baseline_entry_id) : null,
    entries,
  };
}

async function readSweepDecisionStore() {
  try {
    const raw = await fsp.readFile(SWEEP_DECISION_STORE_PATH, "utf8");
    return normalizeSweepDecisionStore(JSON.parse(raw));
  } catch (error) {
    if (error && error.code === "ENOENT") return defaultSweepDecisionStore();
    throw error;
  }
}

async function writeSweepDecisionStore(store) {
  const normalized = normalizeSweepDecisionStore(store);
  normalized.updated_at = new Date().toISOString();
  await fsp.mkdir(path.dirname(SWEEP_DECISION_STORE_PATH), { recursive: true });
  await fsp.writeFile(SWEEP_DECISION_STORE_PATH, `${JSON.stringify(normalized, null, 2)}\n`, "utf8");
  return normalized;
}

function defaultShellWorkspaceStore() {
  return {
    version: 1,
    updated_at: null,
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
    const runIds = Array.isArray(tab.runIds) ? tab.runIds.filter((value) => typeof value === "string" && value) : [];
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

function normalizeShellWorkspaceStore(store) {
  const fallback = defaultShellWorkspaceStore();
  if (!store || typeof store !== "object") return fallback;

  const selectedRunIds = Array.isArray(store.selected_run_ids)
    ? store.selected_run_ids.filter((value) => typeof value === "string" && value).slice(0, 4)
    : [];
  const launchForm = store.launch_form && typeof store.launch_form === "object"
    ? {
        command: store.launch_form.command === "sweep" ? "sweep" : "run",
        ticker: typeof store.launch_form.ticker === "string" ? store.launch_form.ticker : "",
        start: typeof store.launch_form.start === "string" ? store.launch_form.start : "",
        end: typeof store.launch_form.end === "string" ? store.launch_form.end : "",
        interval: typeof store.launch_form.interval === "string" ? store.launch_form.interval : "",
        cash: typeof store.launch_form.cash === "string" ? store.launch_form.cash : "",
        paper: Boolean(store.launch_form.paper),
        config_path: typeof store.launch_form.config_path === "string" ? store.launch_form.config_path : "",
        out_dir: typeof store.launch_form.out_dir === "string" ? store.launch_form.out_dir : "",
      }
    : fallback.launch_form;
  const tabs = Array.isArray(store.tabs) ? store.tabs.map(normalizeShellTab).filter(Boolean) : [];
  const activeTabId = typeof store.active_tab_id === "string" ? store.active_tab_id : null;

  return {
    version: 1,
    updated_at: store.updated_at || null,
    active_tab_id: tabs.some((tab) => tab.id === activeTabId) ? activeTabId : tabs[0]?.id || null,
    selected_run_ids: selectedRunIds,
    tabs,
    launch_form: launchForm,
  };
}

async function readShellWorkspaceStore() {
  try {
    const raw = await fsp.readFile(WORKSPACE_STORE_PATH, "utf8");
    return normalizeShellWorkspaceStore(JSON.parse(raw));
  } catch (error) {
    if (error && error.code === "ENOENT") return defaultShellWorkspaceStore();
    if (error instanceof SyntaxError) return defaultShellWorkspaceStore();
    throw error;
  }
}

async function writeShellWorkspaceStore(store) {
  const normalized = normalizeShellWorkspaceStore(store);
  normalized.updated_at = new Date().toISOString();
  await fsp.mkdir(path.dirname(WORKSPACE_STORE_PATH), { recursive: true });
  const tempPath = `${WORKSPACE_STORE_PATH}.tmp`;
  await fsp.writeFile(tempPath, `${JSON.stringify(normalized, null, 2)}\n`, "utf8");
  await fsp.rename(tempPath, WORKSPACE_STORE_PATH);
  return normalized;
}

async function listDirectoryEntries(targetPath, maxDepth = 2) {
  const safePath = assertPathInsideProject(targetPath);
  const rootStats = await fsp.stat(safePath);
  if (!rootStats.isDirectory()) {
    throw new Error("Requested path is not a directory.");
  }

  const entries = [];

  async function walk(currentPath, depth) {
    const dirEntries = await fsp.readdir(currentPath, { withFileTypes: true });
    for (const entry of dirEntries.sort((left, right) => {
      const leftRank = left.isDirectory() ? 0 : 1;
      const rightRank = right.isDirectory() ? 0 : 1;
      if (leftRank !== rightRank) return leftRank - rightRank;
      return left.name.localeCompare(right.name);
    })) {
      if (entries.length >= MAX_DIRECTORY_ENTRIES) return;
      const absolutePath = path.join(currentPath, entry.name);
      const stats = await fsp.stat(absolutePath);
      entries.push({
        name: entry.name,
        path: absolutePath,
        relative_path: path.relative(safePath, absolutePath),
        kind: entry.isDirectory() ? "directory" : "file",
        size_bytes: stats.size,
        modified_at: stats.mtime.toISOString(),
        depth,
      });
      if (entry.isDirectory() && depth < maxDepth) {
        await walk(absolutePath, depth + 1);
      }
    }
  }

  await walk(safePath, 0);
  return {
    root_path: safePath,
    entries,
    truncated: entries.length >= MAX_DIRECTORY_ENTRIES,
  };
}

async function readProjectText(targetPath) {
  const safePath = assertPathInsideProject(targetPath);
  const stats = await fsp.stat(safePath);
  if (!stats.isFile()) {
    throw new Error("Requested path is not a file.");
  }
  return fsp.readFile(safePath, "utf8");
}

async function readProjectJson(targetPath) {
  const raw = await readProjectText(targetPath);
  try {
    return JSON.parse(raw);
  } catch (_error) {
    const sanitized = raw
      .replace(/\bNaN\b/g, "null")
      .replace(/\b-Infinity\b/g, "null")
      .replace(/\bInfinity\b/g, "null");
    return JSON.parse(sanitized);
  }
}

function parseYamlSectionValue(raw, sectionName, keyName) {
  const sectionPattern = new RegExp(`^${sectionName}:\\s*\\r?\\n([\\s\\S]*?)(?=^\\S|\\Z)`, "m");
  const sectionMatch = String(raw || "").match(sectionPattern);
  if (!sectionMatch) return "";
  const keyPattern = new RegExp(`^\\s*${keyName}:\\s*"?([^"\\r\\n]+)"?`, "m");
  const keyMatch = sectionMatch[1].match(keyPattern);
  return keyMatch ? String(keyMatch[1]).trim() : "";
}

function normalizeStepbitHost(rawHost) {
  const fallback = "127.0.0.1";
  const value = String(rawHost || "").trim();
  if (!value) return fallback;
  return value.replace(/^https?:\/\//i, "").replace(/\/+$/, "") || fallback;
}

function normalizeStepbitPort(rawPort) {
  const match = String(rawPort || "").match(/(\d{2,5})/);
  return match ? match[1] : "8080";
}

async function readStepbitAppConfig() {
  const fallback = {
    host: "127.0.0.1",
    port: "8080",
    apiKey: "sk-dev-key-123",
    apiBaseUrl: "http://127.0.0.1:8080/api",
  };
  try {
    const raw = await fsp.readFile(STEPBIT_APP_CONFIG_PATH, "utf8");
    const host = normalizeStepbitHost(parseYamlSectionValue(raw, "server", "host"));
    const port = normalizeStepbitPort(parseYamlSectionValue(raw, "server", "port"));
    const apiKey = parseYamlSectionValue(raw, "server", "key") || fallback.apiKey;
    return {
      host,
      port,
      apiKey,
      apiBaseUrl: `http://${host}:${port}/api`,
    };
  } catch (error) {
    if (error && error.code === "ENOENT") return fallback;
    throw error;
  }
}

function extractStepbitDelta(payload) {
  const choice = payload?.choices?.[0];
  if (!choice || typeof choice !== "object") return { content: "", reasoning: "", error: payload?.error || "" };
  const delta = choice.delta && typeof choice.delta === "object" ? choice.delta : {};
  return {
    content: typeof delta.content === "string" ? delta.content : "",
    reasoning: typeof delta.reasoning_content === "string" ? delta.reasoning_content : "",
    error: typeof payload.error === "string" ? payload.error : "",
  };
}

async function readStepbitSseResponse(response) {
  if (!response.body || typeof response.body.getReader !== "function") {
    throw new Error("Stepbit returned an unreadable response body.");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let content = "";
  let reasoningSeen = false;
  let tokenEvents = 0;

  function processEventBlock(block) {
    const lines = String(block || "").split(/\r?\n/);
    for (const line of lines) {
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      if (!payload) continue;
      if (payload === "[DONE]") return true;
      let parsed;
      try {
        parsed = JSON.parse(payload);
      } catch (_error) {
        continue;
      }
      const delta = extractStepbitDelta(parsed);
      if (delta.error) {
        throw new Error(delta.error);
      }
      if (delta.reasoning) reasoningSeen = true;
      if (delta.content) {
        content += delta.content;
        tokenEvents += 1;
      }
    }
    return false;
  }

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    let boundaryIndex = buffer.indexOf("\n\n");
    while (boundaryIndex >= 0) {
      const block = buffer.slice(0, boundaryIndex);
      buffer = buffer.slice(boundaryIndex + 2);
      if (processEventBlock(block)) {
        return {
          content: content.trim(),
          reasoningSeen,
          tokenEvents,
        };
      }
      boundaryIndex = buffer.indexOf("\n\n");
    }
    if (done) break;
  }

  if (buffer.trim()) processEventBlock(buffer);
  return {
    content: content.trim(),
    reasoningSeen,
    tokenEvents,
  };
}

async function askStepbitChat(payload) {
  const prompt = String(payload?.prompt || "").trim();
  const messages = Array.isArray(payload?.messages) ? payload.messages : [];
  if (!prompt || !messages.length) {
    throw new Error("Stepbit adapter needs a prompt and at least one message.");
  }

  const config = await readStepbitAppConfig();
  const endpoint = `${config.apiBaseUrl}/v1/chat/completions`;
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.apiKey}`,
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      model: typeof payload?.model === "string" ? payload.model : "",
      messages,
      stream: true,
      search: Boolean(payload?.search),
      reason: Boolean(payload?.reason),
      max_tokens: Number.isFinite(Number(payload?.max_tokens)) ? Number(payload.max_tokens) : undefined,
      temperature: Number.isFinite(Number(payload?.temperature)) ? Number(payload.temperature) : undefined,
    }),
  });

  if (!response.ok) {
    let errorMessage = `Stepbit chat returned ${response.status}.`;
    try {
      const bodyText = await response.text();
      if (bodyText) {
        try {
          const data = JSON.parse(bodyText);
          errorMessage = data.error || data.message || errorMessage;
        } catch (_error) {
          errorMessage = bodyText.trim() || errorMessage;
        }
      }
    } catch (_error) {
      // Ignore body parse failures and return the HTTP-derived message.
    }
    if (response.status === 401) {
      throw new Error("Stepbit rejected the local API key from config.yaml.");
    }
    throw new Error(errorMessage);
  }

  const result = await readStepbitSseResponse(response);
  if (!result.content) {
    throw new Error("Stepbit returned no final content for this request.");
  }
  return {
    ...result,
    endpoint,
  };
}

function appendLog(line) {
  if (!line) return;
  workspaceState.logs = [...workspaceState.logs.slice(-49), line];
  broadcastWorkspaceState();
}

function updateWorkspaceState(patch) {
  workspaceState = {
    ...workspaceState,
    ...patch,
  };
  broadcastWorkspaceState();
}

function broadcastWorkspaceState() {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  mainWindow.webContents.send("quantlab:workspace-state", workspaceState);
}

function clearResearchStartupTimer() {
  if (researchStartupTimer) {
    clearTimeout(researchStartupTimer);
    researchStartupTimer = null;
  }
}

function scheduleResearchStartupTimeout() {
  clearResearchStartupTimer();
  researchStartupTimer = setTimeout(() => {
    if (workspaceState.status === "ready") return;
    updateWorkspaceState({
      status: "error",
      error: "research_ui did not become ready before the startup timeout.",
    });
    appendLog("[startup-timeout] research_ui did not become ready before the timeout.");
  }, RESEARCH_UI_STARTUP_TIMEOUT_MS);
}

async function isResearchUiReachable(baseUrl) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 1000);
  try {
    const response = await fetch(`${String(baseUrl).replace(/\/$/, "")}${RESEARCH_UI_HEALTH_PATH}`, {
      signal: controller.signal,
      headers: { "User-Agent": "QuantLab-Desktop" },
    });
    return response.ok;
  } catch (_error) {
    return false;
  } finally {
    clearTimeout(timeout);
  }
}

async function detectResearchUiServerUrl() {
  for (const candidate of RESEARCH_UI_URLS) {
    if (await isResearchUiReachable(candidate)) return candidate;
  }
  return "";
}

function markResearchUiReady(discoveredUrl, source) {
  clearResearchStartupTimer();
  updateWorkspaceState({
    status: "ready",
    serverUrl: discoveredUrl,
    error: null,
    source,
  });
}

async function monitorResearchUiStartup() {
  const deadline = Date.now() + RESEARCH_UI_STARTUP_TIMEOUT_MS;
  while (researchServerProcess && Date.now() < deadline) {
    const discoveredUrl = await detectResearchUiServerUrl();
    if (discoveredUrl) {
      markResearchUiReady(discoveredUrl, researchServerOwned ? "managed" : "external");
      appendLog(`[startup] research_ui reachable at ${discoveredUrl}`);
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
}

function resolvePythonCandidates() {
  const isWindows = process.platform === "win32";
  const localVenv = path.join(PROJECT_ROOT, ".venv", isWindows ? "Scripts" : "bin", isWindows ? "python.exe" : "python");
  const candidates = [
    localVenv,
    process.env.PYTHON || "",
    isWindows ? "python" : "python3",
  ]
    .map((value) => String(value || "").trim())
    .filter(Boolean);

  return [...new Set(candidates)].filter((candidate) => {
    if (!path.isAbsolute(candidate)) return true;
    try {
      fs.accessSync(candidate, fs.constants.R_OK);
      return true;
    } catch (_error) {
      return false;
    }
  });
}

function bindResearchUiProcess(processHandle, pythonCommand, candidates, candidateIndex) {
  researchServerProcess = processHandle;
  researchServerOwned = true;

  processHandle.stdout.setEncoding("utf8");
  processHandle.stderr.setEncoding("utf8");
  monitorResearchUiStartup().catch((error) => {
    appendLog(`[startup-monitor-error] ${error.message}`);
  });

  processHandle.stdout.on("data", (chunk) => {
    String(chunk || "")
      .split(/\r?\n/)
      .forEach((line) => {
        if (!line.trim()) return;
        appendLog(line);
        const discoveredUrl = extractServerUrl(line);
        if (discoveredUrl) {
          isResearchUiReachable(discoveredUrl)
            .then((reachable) => {
              if (!reachable || !researchServerProcess || researchServerProcess !== processHandle) return;
              markResearchUiReady(discoveredUrl, "managed");
            })
            .catch(() => {});
        }
      });
  });

  processHandle.stderr.on("data", (chunk) => {
    String(chunk || "")
      .split(/\r?\n/)
      .forEach((line) => {
        if (!line.trim()) return;
        appendLog(`[stderr] ${line}`);
      });
  });

  processHandle.on("exit", (code, signal) => {
    if (researchServerProcess !== processHandle) return;
    researchServerProcess = null;
    researchServerOwned = false;
    const shouldRetry = code !== 0 && workspaceState.status === "starting" && candidateIndex < candidates.length - 1;
    if (shouldRetry) {
      const nextCommand = candidates[candidateIndex + 1];
      appendLog(`[startup-exit] ${pythonCommand} exited (${code ?? "null"}${signal ? `, ${signal}` : ""}). Retrying with ${nextCommand}.`);
      launchResearchUiProcess(candidates, candidateIndex + 1);
      return;
    }
    clearResearchStartupTimer();
    updateWorkspaceState({
      status: "stopped",
      serverUrl: null,
      error: code === 0 ? null : `research_ui exited (${code ?? "null"}${signal ? `, ${signal}` : ""})`,
      source: "managed",
    });
  });

  processHandle.on("error", (error) => {
    if (researchServerProcess === processHandle) {
      researchServerProcess = null;
      researchServerOwned = false;
    }
    const shouldRetry =
      ["EACCES", "EPERM", "ENOENT"].includes(error?.code || "") &&
      candidateIndex < candidates.length - 1;
    if (shouldRetry) {
      const nextCommand = candidates[candidateIndex + 1];
      appendLog(`[spawn-error] ${pythonCommand} failed (${error.code}). Retrying with ${nextCommand}.`);
      launchResearchUiProcess(candidates, candidateIndex + 1);
      return;
    }
    clearResearchStartupTimer();
    updateWorkspaceState({
      status: "error",
      serverUrl: null,
      error: error.message,
      source: "managed",
    });
    appendLog(`[spawn-error] ${error.message}`);
  });
}

function launchResearchUiProcess(candidates, candidateIndex = 0) {
  const pythonCommand = candidates[candidateIndex];
  appendLog(`[startup] launching research_ui with ${pythonCommand}`);
  const child = spawn(pythonCommand, [SERVER_SCRIPT], {
    cwd: PROJECT_ROOT,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });
  bindResearchUiProcess(child, pythonCommand, candidates, candidateIndex);
}

function extractServerUrl(line) {
  const match = String(line).match(/URL:\s*(http:\/\/[^\s]+)/i);
  return match ? match[1] : null;
}

async function startResearchUiServer({ forceRestart = false } = {}) {
  if (forceRestart) {
    stopResearchUiServer({ force: true });
  }

  if (researchServerProcess) return;

  const existingUrl = await detectResearchUiServerUrl();
  if (existingUrl) {
    researchServerOwned = false;
    markResearchUiReady(existingUrl, "external");
    appendLog(`[startup] reusing existing research_ui server at ${existingUrl}`);
    return;
  }

  updateWorkspaceState({
    status: "starting",
    serverUrl: null,
    error: null,
    source: "managed",
  });
  scheduleResearchStartupTimeout();

  const pythonCandidates = resolvePythonCandidates();
  if (!pythonCandidates.length) {
    clearResearchStartupTimer();
    updateWorkspaceState({
      status: "error",
      serverUrl: null,
      error: "No usable Python interpreter was found for research_ui startup.",
      source: "managed",
    });
    return;
  }

  launchResearchUiProcess(pythonCandidates, 0);
}

function stopResearchUiServer({ force = false } = {}) {
  clearResearchStartupTimer();
  if (!researchServerProcess || !researchServerOwned) return;
  try {
    if (process.platform === "win32" && researchServerProcess.pid) {
      spawn("taskkill", ["/PID", String(researchServerProcess.pid), "/T", "/F"], {
        windowsHide: true,
        stdio: "ignore",
      });
    } else {
      researchServerProcess.kill(force ? "SIGKILL" : "SIGTERM");
    }
  } catch (_error) {
    // Best effort shutdown.
  }
  researchServerProcess = null;
  researchServerOwned = false;
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1100,
    minHeight: 760,
    show: !IS_SMOKE_RUN,
    autoHideMenuBar: true,
    backgroundColor: "#0b1118",
    title: "QuantLab Desktop",
    webPreferences: {
      preload: path.join(DESKTOP_ROOT, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  mainWindow.loadFile(path.join(DESKTOP_ROOT, "renderer", "index.html"));
  if (!IS_SMOKE_RUN) {
    mainWindow.once("ready-to-show", () => {
      if (!mainWindow || mainWindow.isDestroyed()) return;
      mainWindow.show();
    });
  }
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

async function runDesktopSmoke() {
  const result = {
    bridgeReady: false,
    serverReady: false,
    apiReady: false,
    serverUrl: "",
    error: "",
  };
  try {
    result.bridgeReady = await mainWindow.webContents.executeJavaScript(
      "Boolean(window.quantlabDesktop && typeof window.quantlabDesktop.getWorkspaceState === 'function')",
      true,
    );
    const deadline = Date.now() + RESEARCH_UI_STARTUP_TIMEOUT_MS;
    while (Date.now() < deadline) {
      if (workspaceState.serverUrl && await isResearchUiReachable(workspaceState.serverUrl)) {
        result.serverReady = true;
        result.apiReady = true;
        result.serverUrl = workspaceState.serverUrl;
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
    if (!result.serverReady) {
      result.error = workspaceState.error || "research_ui did not become reachable during smoke run.";
    }
  } catch (error) {
    result.error = error.message;
  }

  if (SMOKE_OUTPUT_PATH) {
    await fsp.mkdir(path.dirname(SMOKE_OUTPUT_PATH), { recursive: true });
    await fsp.writeFile(SMOKE_OUTPUT_PATH, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  }

  if (!result.bridgeReady || !result.serverReady || !result.apiReady) {
    process.exitCode = 1;
  }
  app.quit();
}

ipcMain.handle("quantlab:get-workspace-state", async () => workspaceState);

ipcMain.handle("quantlab:request-json", async (_event, relativePath) => {
  if (!workspaceState.serverUrl) {
    throw new Error("Research UI server is not ready yet.");
  }
  const base = workspaceState.serverUrl.replace(/\/$/, "");
  const response = await fetch(`${base}${relativePath}`);
  if (!response.ok) {
    throw new Error(`${relativePath} returned ${response.status}`);
  }
  return response.json();
});

ipcMain.handle("quantlab:request-text", async (_event, relativePath) => {
  if (!workspaceState.serverUrl) {
    throw new Error("Research UI server is not ready yet.");
  }
  const base = workspaceState.serverUrl.replace(/\/$/, "");
  const response = await fetch(`${base}${relativePath}`);
  if (!response.ok) {
    throw new Error(`${relativePath} returned ${response.status}`);
  }
  return response.text();
});

ipcMain.handle("quantlab:get-candidates-store", async () => readCandidatesStore());

ipcMain.handle("quantlab:save-candidates-store", async (_event, payload) => writeCandidatesStore(payload));

ipcMain.handle("quantlab:get-sweep-decision-store", async () => readSweepDecisionStore());

ipcMain.handle("quantlab:save-sweep-decision-store", async (_event, payload) => writeSweepDecisionStore(payload));

ipcMain.handle("quantlab:get-shell-workspace-store", async () => readShellWorkspaceStore());

ipcMain.handle("quantlab:save-shell-workspace-store", async (_event, payload) => writeShellWorkspaceStore(payload));

ipcMain.handle("quantlab:list-directory", async (_event, targetPath, maxDepth = 2) => {
  return listDirectoryEntries(targetPath, maxDepth);
});

ipcMain.handle("quantlab:read-project-text", async (_event, targetPath) => {
  return readProjectText(targetPath);
});

ipcMain.handle("quantlab:read-project-json", async (_event, targetPath) => {
  return readProjectJson(targetPath);
});

ipcMain.handle("quantlab:post-json", async (_event, relativePath, payload) => {
  if (!workspaceState.serverUrl) {
    throw new Error("Research UI server is not ready yet.");
  }
  const base = workspaceState.serverUrl.replace(/\/$/, "");
  const response = await fetch(`${base}${relativePath}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload ?? {}),
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(data.message || `${relativePath} returned ${response.status}`);
  }
  return data;
});

ipcMain.handle("quantlab:open-external", async (_event, url) => {
  await shell.openExternal(url);
});

ipcMain.handle("quantlab:open-path", async (_event, targetPath) => {
  const safePath = assertPathInsideProject(targetPath);
  const errorMessage = await shell.openPath(safePath);
  if (errorMessage) throw new Error(errorMessage);
  return { ok: true };
});

ipcMain.handle("quantlab:restart-workspace-server", async () => {
  await startResearchUiServer({ forceRestart: true });
  return workspaceState;
});

ipcMain.handle("quantlab:ask-stepbit-chat", async (_event, payload) => {
  return askStepbitChat(payload);
});

if (singleInstanceLock) {
  app.on("second-instance", () => {
    if (!mainWindow || mainWindow.isDestroyed()) return;
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  });

  app.whenReady().then(() => {
    createMainWindow();
    startResearchUiServer();
    if (IS_SMOKE_RUN) {
      mainWindow.webContents.once("did-finish-load", () => {
        runDesktopSmoke().catch((error) => {
          if (SMOKE_OUTPUT_PATH) {
            fsp.mkdir(path.dirname(SMOKE_OUTPUT_PATH), { recursive: true })
              .then(() => fsp.writeFile(SMOKE_OUTPUT_PATH, `${JSON.stringify({ bridgeReady: false, serverReady: false, apiReady: false, error: error.message }, null, 2)}\n`, "utf8"))
              .finally(() => {
                process.exitCode = 1;
                app.quit();
              });
          } else {
            process.exitCode = 1;
            app.quit();
          }
        });
      });
    }

    app.on("activate", () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createMainWindow();
      }
    });
  });
}

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  stopResearchUiServer();
});
