// @ts-check

/** @typedef {import("../shared/models/workspace").WorkspaceState} WorkspaceState */
/** @typedef {import("../shared/models/workspace").WorkspaceStatePatch} WorkspaceStatePatch */

const WORKSPACE_STATE_CHANNEL = "quantlab:workspace-state";

/**
 * @param {{ getMainWindow: () => import("electron").BrowserWindow | null }} options
 */
function createWorkspaceStateController({ getMainWindow }) {
  /** @type {WorkspaceState} */
  let workspaceState = {
    status: "idle",
    serverUrl: null,
    logs: [],
    error: null,
    source: null,
  };

  function getState() {
    return workspaceState;
  }

  function broadcast() {
    const mainWindow = getMainWindow();
    if (!mainWindow || mainWindow.isDestroyed()) return;
    mainWindow.webContents.send(WORKSPACE_STATE_CHANNEL, workspaceState);
  }

  function appendLog(line) {
    if (!line) return;
    workspaceState.logs = [...workspaceState.logs.slice(-49), line];
    broadcast();
  }

  /**
   * @param {WorkspaceStatePatch} patch
   */
  function update(patch) {
    workspaceState = {
      ...workspaceState,
      ...patch,
    };
    broadcast();
  }

  return {
    getState,
    broadcast,
    appendLog,
    update,
  };
}

module.exports = { createWorkspaceStateController };
