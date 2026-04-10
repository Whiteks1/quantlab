// @ts-check

const { app, BrowserWindow, ipcMain, shell } = require("electron");
const fs = require("fs");
const fsp = require("fs/promises");
const path = require("path");
const { spawn } = require("child_process");

const config = require("./main/config.js");
const { createLocalStoreService } = require("./main/local-store-service.js");
const { registerIpcHandlers } = require("./main/register-ipc.js");
const { createResearchUiService } = require("./main/research-ui-service.js");
const { createSmokeService } = require("./main/smoke-service.js");
const { createStepbitService } = require("./main/stepbit-service.js");
const { createMainWindow } = require("./main/window.js");
const { createWorkspaceStateController } = require("./main/workspace-state.js");

app.setPath("userData", path.join(config.ELECTRON_STATE_ROOT, "user-data"));
app.setPath("cache", path.join(config.ELECTRON_STATE_ROOT, "cache"));

const singleInstanceLock = app.requestSingleInstanceLock();
if (!singleInstanceLock) {
  app.quit();
  process.exit(0);
}

/** @type {import("electron").BrowserWindow | null} */
let mainWindow = null;

const workspace = createWorkspaceStateController({
  getMainWindow: () => mainWindow,
});

const localStores = createLocalStoreService({
  fs,
  fsp,
  path,
  projectRoot: config.PROJECT_ROOT,
  candidatesStorePath: config.CANDIDATES_STORE_PATH,
  sweepDecisionStorePath: config.SWEEP_DECISION_STORE_PATH,
  workspaceStorePath: config.WORKSPACE_STORE_PATH,
  maxDirectoryEntries: config.MAX_DIRECTORY_ENTRIES,
});

const stepbit = createStepbitService({
  fsp,
  stepbitAppConfigPath: config.STEPBIT_APP_CONFIG_PATH,
});

const researchUi = createResearchUiService({
  fs,
  path,
  spawn,
  projectRoot: config.PROJECT_ROOT,
  serverScript: config.SERVER_SCRIPT,
  researchUiUrls: config.RESEARCH_UI_URLS,
  healthPath: config.RESEARCH_UI_HEALTH_PATH,
  startupTimeoutMs: config.RESEARCH_UI_STARTUP_TIMEOUT_MS,
  workspace,
});

const smoke = createSmokeService({
  app,
  fsp,
  path,
  smokeOutputPath: config.SMOKE_OUTPUT_PATH,
  smokeMode: config.SMOKE_MODE,
  startupTimeoutMs: config.RESEARCH_UI_STARTUP_TIMEOUT_MS,
  outputsRoot: config.OUTPUTS_ROOT,
  workspace,
  researchUi,
  localStores,
  getMainWindow: () => mainWindow,
});

registerIpcHandlers({
  ipcMain,
  shell,
  workspace,
  localStores,
  researchUi,
  stepbit,
});

function openMainWindow() {
  mainWindow = createMainWindow({
    BrowserWindow,
    desktopRoot: config.DESKTOP_ROOT,
    isSmokeRun: config.IS_SMOKE_RUN,
    onClosed: () => {
      mainWindow = null;
    },
  });
  return mainWindow;
}

/**
 * @param {import("electron").BrowserWindow} window
 */
function attachSmokeHandlers(window) {
  if (!config.IS_SMOKE_RUN) return;
  window.webContents.once("did-fail-load", (_event, errorCode, errorDescription) => {
    smoke.failAndQuit(`Desktop smoke load failed: ${errorDescription || `code ${errorCode}`}`);
  });
  window.webContents.once("render-process-gone", (_event, details) => {
    smoke.failAndQuit(`Desktop smoke renderer exited before completion: ${details?.reason || "unknown"}`);
  });
  window.webContents.once("did-finish-load", () => {
    smoke.markDidFinishLoadSeen();
    smoke.run().catch((error) => {
      smoke.failAndQuit(error.message);
    });
  });
}

app.on("second-instance", () => {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  if (mainWindow.isMinimized()) mainWindow.restore();
  mainWindow.focus();
});

app.whenReady().then(() => {
  const window = openMainWindow();
  if (!config.SKIP_RESEARCH_UI_BOOT) {
    researchUi.start().catch((error) => {
      workspace.appendLog(`[startup-error] ${error.message}`);
      workspace.update({
        status: "error",
        serverUrl: null,
        error: error.message,
        source: "managed",
      });
    });
  }
  attachSmokeHandlers(window);

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      openMainWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (config.IS_SMOKE_RUN && !smoke.hasPersistedResult()) {
    smoke.failAndQuit(
      smoke.didFinishLoad()
        ? "Desktop smoke window closed before the result was persisted."
        : "Desktop smoke window closed before the renderer finished loading.",
    );
    return;
  }
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  researchUi.stop();
});

process.on("uncaughtException", (error) => {
  if (!config.IS_SMOKE_RUN) throw error;
  smoke.failAndQuit(`Desktop smoke uncaught exception: ${error?.message || String(error)}`);
});

process.on("unhandledRejection", (reason) => {
  if (!config.IS_SMOKE_RUN) throw reason;
  const message = reason instanceof Error ? reason.message : String(reason);
  smoke.failAndQuit(`Desktop smoke unhandled rejection: ${message}`);
});
