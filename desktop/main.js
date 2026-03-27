const { app, BrowserWindow, ipcMain, shell } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

const DESKTOP_ROOT = __dirname;
const PROJECT_ROOT = path.resolve(DESKTOP_ROOT, "..");
const SERVER_SCRIPT = path.join(PROJECT_ROOT, "research_ui", "server.py");

let mainWindow = null;
let researchServerProcess = null;
let workspaceState = {
  status: "idle",
  serverUrl: null,
  logs: [],
  error: null,
};

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
