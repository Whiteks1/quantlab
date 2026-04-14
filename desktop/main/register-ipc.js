// @ts-check

/** @typedef {import("../shared/ipc/channels").GetWorkspaceStateChannel} GetWorkspaceStateChannel */
/** @typedef {import("../shared/ipc/channels").RequestJsonChannel} RequestJsonChannel */
/** @typedef {import("../shared/ipc/channels").RequestTextChannel} RequestTextChannel */
/** @typedef {import("../shared/ipc/channels").GetCandidatesStoreChannel} GetCandidatesStoreChannel */
/** @typedef {import("../shared/ipc/channels").SaveCandidatesStoreChannel} SaveCandidatesStoreChannel */
/** @typedef {import("../shared/ipc/channels").GetSweepDecisionStoreChannel} GetSweepDecisionStoreChannel */
/** @typedef {import("../shared/ipc/channels").SaveSweepDecisionStoreChannel} SaveSweepDecisionStoreChannel */
/** @typedef {import("../shared/ipc/channels").GetShellWorkspaceStoreChannel} GetShellWorkspaceStoreChannel */
/** @typedef {import("../shared/ipc/channels").SaveShellWorkspaceStoreChannel} SaveShellWorkspaceStoreChannel */
/** @typedef {import("../shared/ipc/channels").ListDirectoryChannel} ListDirectoryChannel */
/** @typedef {import("../shared/ipc/channels").ReadProjectTextChannel} ReadProjectTextChannel */
/** @typedef {import("../shared/ipc/channels").ReadProjectJsonChannel} ReadProjectJsonChannel */
/** @typedef {import("../shared/ipc/channels").PostJsonChannel} PostJsonChannel */
/** @typedef {import("../shared/ipc/channels").OpenExternalChannel} OpenExternalChannel */
/** @typedef {import("../shared/ipc/channels").OpenPathChannel} OpenPathChannel */
/** @typedef {import("../shared/ipc/channels").RestartWorkspaceServerChannel} RestartWorkspaceServerChannel */
/** @typedef {import("../shared/ipc/channels").AskStepbitChatChannel} AskStepbitChatChannel */

/** @type {GetWorkspaceStateChannel} */
const GET_WORKSPACE_STATE_CHANNEL = "quantlab:get-workspace-state";
/** @type {RequestJsonChannel} */
const REQUEST_JSON_CHANNEL = "quantlab:request-json";
/** @type {RequestTextChannel} */
const REQUEST_TEXT_CHANNEL = "quantlab:request-text";
/** @type {GetCandidatesStoreChannel} */
const GET_CANDIDATES_STORE_CHANNEL = "quantlab:get-candidates-store";
/** @type {SaveCandidatesStoreChannel} */
const SAVE_CANDIDATES_STORE_CHANNEL = "quantlab:save-candidates-store";
/** @type {GetSweepDecisionStoreChannel} */
const GET_SWEEP_DECISION_STORE_CHANNEL = "quantlab:get-sweep-decision-store";
/** @type {SaveSweepDecisionStoreChannel} */
const SAVE_SWEEP_DECISION_STORE_CHANNEL = "quantlab:save-sweep-decision-store";
/** @type {GetShellWorkspaceStoreChannel} */
const GET_SHELL_WORKSPACE_STORE_CHANNEL = "quantlab:get-shell-workspace-store";
/** @type {SaveShellWorkspaceStoreChannel} */
const SAVE_SHELL_WORKSPACE_STORE_CHANNEL = "quantlab:save-shell-workspace-store";
/** @type {ListDirectoryChannel} */
const LIST_DIRECTORY_CHANNEL = "quantlab:list-directory";
/** @type {ReadProjectTextChannel} */
const READ_PROJECT_TEXT_CHANNEL = "quantlab:read-project-text";
/** @type {ReadProjectJsonChannel} */
const READ_PROJECT_JSON_CHANNEL = "quantlab:read-project-json";
/** @type {PostJsonChannel} */
const POST_JSON_CHANNEL = "quantlab:post-json";
/** @type {OpenExternalChannel} */
const OPEN_EXTERNAL_CHANNEL = "quantlab:open-external";
/** @type {OpenPathChannel} */
const OPEN_PATH_CHANNEL = "quantlab:open-path";
/** @type {RestartWorkspaceServerChannel} */
const RESTART_WORKSPACE_SERVER_CHANNEL = "quantlab:restart-workspace-server";
/** @type {AskStepbitChatChannel} */
const ASK_STEPBIT_CHAT_CHANNEL = "quantlab:ask-stepbit-chat";

function okIpcResult(data) {
  return { ok: true, data };
}

function errorIpcResult(error) {
  return {
    ok: false,
    error: error?.message || String(error || "Unknown IPC failure."),
  };
}

/**
 * @param {{
 *   ipcMain: typeof import("electron").ipcMain,
 *   shell: typeof import("electron").shell,
 *   workspace: {
 *     getState: () => import("../shared/models/workspace").WorkspaceState,
 *   },
 *   localStores: {
 *     assertPathInsideProject: (targetPath: string) => string,
 *     readCandidatesStore: () => Promise<any>,
 *     writeCandidatesStore: (store: any) => Promise<any>,
 *     readSweepDecisionStore: () => Promise<any>,
 *     writeSweepDecisionStore: (store: any) => Promise<any>,
 *     readShellWorkspaceStore: () => Promise<any>,
 *     writeShellWorkspaceStore: (store: any) => Promise<any>,
 *     listDirectoryEntries: (targetPath: string, maxDepth?: number) => Promise<any>,
 *     readProjectText: (targetPath: string) => Promise<string>,
 *     readProjectJson: (targetPath: string) => Promise<any>,
 *   },
 *   researchUi: {
 *     start: (options?: { forceRestart?: boolean }) => Promise<void>,
 *   },
 *   stepbit: {
 *     askChat: (payload: any) => Promise<any>,
 *   },
 * }} options
 */
function registerIpcHandlers({ ipcMain, shell, workspace, localStores, researchUi, stepbit }) {
  ipcMain.handle(GET_WORKSPACE_STATE_CHANNEL, async () => workspace.getState());

  ipcMain.handle(REQUEST_JSON_CHANNEL, async (_event, relativePath) => {
    try {
      const workspaceState = workspace.getState();
      if (!workspaceState.serverUrl) {
        throw new Error("Research UI server is not ready yet.");
      }
      const base = workspaceState.serverUrl.replace(/\/$/, "");
      const response = await fetch(`${base}${relativePath}`);
      if (!response.ok) {
        throw new Error(`${relativePath} returned ${response.status}`);
      }
      return okIpcResult(await response.json());
    } catch (error) {
      return errorIpcResult(error);
    }
  });

  ipcMain.handle(REQUEST_TEXT_CHANNEL, async (_event, relativePath) => {
    try {
      const workspaceState = workspace.getState();
      if (!workspaceState.serverUrl) {
        throw new Error("Research UI server is not ready yet.");
      }
      const base = workspaceState.serverUrl.replace(/\/$/, "");
      const response = await fetch(`${base}${relativePath}`);
      if (!response.ok) {
        throw new Error(`${relativePath} returned ${response.status}`);
      }
      return okIpcResult(await response.text());
    } catch (error) {
      return errorIpcResult(error);
    }
  });

  ipcMain.handle(GET_CANDIDATES_STORE_CHANNEL, async () => localStores.readCandidatesStore());
  ipcMain.handle(SAVE_CANDIDATES_STORE_CHANNEL, async (_event, payload) => localStores.writeCandidatesStore(payload));

  ipcMain.handle(GET_SWEEP_DECISION_STORE_CHANNEL, async () => localStores.readSweepDecisionStore());
  ipcMain.handle(SAVE_SWEEP_DECISION_STORE_CHANNEL, async (_event, payload) => localStores.writeSweepDecisionStore(payload));

  ipcMain.handle(GET_SHELL_WORKSPACE_STORE_CHANNEL, async () => localStores.readShellWorkspaceStore());
  ipcMain.handle(SAVE_SHELL_WORKSPACE_STORE_CHANNEL, async (_event, payload) => localStores.writeShellWorkspaceStore(payload));

  ipcMain.handle(LIST_DIRECTORY_CHANNEL, async (_event, targetPath, maxDepth = 2) => {
    return localStores.listDirectoryEntries(targetPath, maxDepth);
  });

  ipcMain.handle(READ_PROJECT_TEXT_CHANNEL, async (_event, targetPath) => {
    return localStores.readProjectText(targetPath);
  });

  ipcMain.handle(READ_PROJECT_JSON_CHANNEL, async (_event, targetPath) => {
    return localStores.readProjectJson(targetPath);
  });

  ipcMain.handle(POST_JSON_CHANNEL, async (_event, relativePath, payload) => {
    try {
      const workspaceState = workspace.getState();
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
      return okIpcResult(data);
    } catch (error) {
      return errorIpcResult(error);
    }
  });

  ipcMain.handle(OPEN_EXTERNAL_CHANNEL, async (_event, url) => {
    await shell.openExternal(url);
  });

  ipcMain.handle(OPEN_PATH_CHANNEL, async (_event, targetPath) => {
    const safePath = localStores.assertPathInsideProject(targetPath);
    const errorMessage = await shell.openPath(safePath);
    if (errorMessage) throw new Error(errorMessage);
    return { ok: true };
  });

  ipcMain.handle(RESTART_WORKSPACE_SERVER_CHANNEL, async () => {
    await researchUi.start({ forceRestart: true });
    return workspace.getState();
  });

  ipcMain.handle(ASK_STEPBIT_CHAT_CHANNEL, async (_event, payload) => {
    return stepbit.askChat(payload);
  });
}

module.exports = { registerIpcHandlers };
