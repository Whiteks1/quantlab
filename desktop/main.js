const { app, BrowserWindow, ipcMain, shell } = require("electron");
const fs = require("fs");
const fsp = require("fs/promises");
const path = require("path");
const { spawn } = require("child_process");

const DESKTOP_ROOT = __dirname;
const PROJECT_ROOT = path.resolve(DESKTOP_ROOT, "..");
const SERVER_SCRIPT = path.join(PROJECT_ROOT, "research_ui", "server.py");
const OUTPUTS_ROOT = path.join(PROJECT_ROOT, "outputs");
const DESKTOP_OUTPUTS_ROOT = path.join(OUTPUTS_ROOT, "desktop");
const CANDIDATES_STORE_PATH = path.join(DESKTOP_OUTPUTS_ROOT, "candidates_shortlist.json");
const SWEEP_DECISION_STORE_PATH = path.join(DESKTOP_OUTPUTS_ROOT, "sweep_decision_handoff.json");
const MAX_DIRECTORY_ENTRIES = 240;

let mainWindow = null;
let researchServerProcess = null;
let workspaceState = {
  status: "idle",
  serverUrl: null,
  logs: [],
  error: null,
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

function appendLog(line) {
  if (!line) return;
  workspaceState.logs = [...workspaceState.logs.slice(-49), line];
  broadcastWorkspaceState();
}

function broadcastWorkspaceState() {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  mainWindow.webContents.send("quantlab:workspace-state", workspaceState);
}

function resolvePythonCommand() {
  const isWindows = process.platform === "win32";
  const localVenv = path.join(PROJECT_ROOT, ".venv", isWindows ? "Scripts" : "bin", isWindows ? "python.exe" : "python");
  if (localVenv && require("fs").existsSync(localVenv)) {
    return localVenv;
  }
  return process.env.PYTHON || (isWindows ? "python" : "python3");
}

function extractServerUrl(line) {
  const match = String(line).match(/URL:\s*(http:\/\/[^\s]+)/i);
  return match ? match[1] : null;
}

function startResearchUiServer() {
  if (researchServerProcess) return;

  workspaceState = {
    ...workspaceState,
    status: "starting",
    error: null,
  };
  broadcastWorkspaceState();

  researchServerProcess = spawn(resolvePythonCommand(), [SERVER_SCRIPT], {
    cwd: PROJECT_ROOT,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });

  researchServerProcess.stdout.setEncoding("utf8");
  researchServerProcess.stderr.setEncoding("utf8");

  researchServerProcess.stdout.on("data", (chunk) => {
    String(chunk || "")
      .split(/\r?\n/)
      .forEach((line) => {
        if (!line.trim()) return;
        appendLog(line);
        const discoveredUrl = extractServerUrl(line);
        if (discoveredUrl) {
          workspaceState = {
            ...workspaceState,
            status: "ready",
            serverUrl: discoveredUrl,
            error: null,
          };
          broadcastWorkspaceState();
        }
      });
  });

  researchServerProcess.stderr.on("data", (chunk) => {
    String(chunk || "")
      .split(/\r?\n/)
      .forEach((line) => {
        if (!line.trim()) return;
        appendLog(`[stderr] ${line}`);
      });
  });

  researchServerProcess.on("exit", (code, signal) => {
    researchServerProcess = null;
    workspaceState = {
      ...workspaceState,
      status: "stopped",
      error: code === 0 ? null : `research_ui exited (${code ?? "null"}${signal ? `, ${signal}` : ""})`,
    };
    broadcastWorkspaceState();
  });

  researchServerProcess.on("error", (error) => {
    researchServerProcess = null;
    workspaceState = {
      ...workspaceState,
      status: "error",
      error: error.message,
    };
    appendLog(`[spawn-error] ${error.message}`);
    broadcastWorkspaceState();
  });
}

function stopResearchUiServer() {
  if (!researchServerProcess) return;
  try {
    researchServerProcess.kill();
  } catch (_error) {
    // Best effort shutdown.
  }
  researchServerProcess = null;
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1100,
    minHeight: 760,
    autoHideMenuBar: true,
    backgroundColor: "#0b1118",
    title: "QuantLab Desktop",
    webPreferences: {
      preload: path.join(DESKTOP_ROOT, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  mainWindow.loadFile(path.join(DESKTOP_ROOT, "renderer", "index.html"));
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
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

app.whenReady().then(() => {
  createMainWindow();
  startResearchUiServer();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  stopResearchUiServer();
});
