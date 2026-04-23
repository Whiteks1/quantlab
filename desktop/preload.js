// @ts-nocheck -- legacy JS file, not migrated to strict TypeScript. See #462.

const { contextBridge, ipcRenderer } = require("electron");

/** @typedef {import("./shared/ipc/bridge").QuantlabDesktopBridge} QuantlabDesktopBridge */
/** @typedef {import("./shared/models/workspace").WorkspaceState} WorkspaceState */
/** @typedef {import("./shared/models/workspace").WorkspaceStateListener} WorkspaceStateListener */
/** @typedef {import("./shared/ipc/channels").WorkspaceStateEventChannel} WorkspaceStateEventChannel */
/** @typedef {import("./shared/ipc/channels").GetWorkspaceStateChannel} GetWorkspaceStateChannel */
/** @typedef {import("./shared/ipc/channels").RequestJsonChannel} RequestJsonChannel */
/** @typedef {import("./shared/ipc/channels").RequestTextChannel} RequestTextChannel */
/** @typedef {import("./shared/ipc/channels").GetCandidatesStoreChannel} GetCandidatesStoreChannel */
/** @typedef {import("./shared/ipc/channels").SaveCandidatesStoreChannel} SaveCandidatesStoreChannel */
/** @typedef {import("./shared/ipc/channels").GetSweepDecisionStoreChannel} GetSweepDecisionStoreChannel */
/** @typedef {import("./shared/ipc/channels").SaveSweepDecisionStoreChannel} SaveSweepDecisionStoreChannel */
/** @typedef {import("./shared/ipc/channels").GetShellWorkspaceStoreChannel} GetShellWorkspaceStoreChannel */
/** @typedef {import("./shared/ipc/channels").SaveShellWorkspaceStoreChannel} SaveShellWorkspaceStoreChannel */
/** @typedef {import("./shared/ipc/channels").ListDirectoryChannel} ListDirectoryChannel */
/** @typedef {import("./shared/ipc/channels").ReadProjectTextChannel} ReadProjectTextChannel */
/** @typedef {import("./shared/ipc/channels").ReadProjectJsonChannel} ReadProjectJsonChannel */
/** @typedef {import("./shared/ipc/channels").PostJsonChannel} PostJsonChannel */
/** @typedef {import("./shared/ipc/channels").OpenExternalChannel} OpenExternalChannel */
/** @typedef {import("./shared/ipc/channels").OpenPathChannel} OpenPathChannel */
/** @typedef {import("./shared/ipc/channels").RestartWorkspaceServerChannel} RestartWorkspaceServerChannel */
/** @typedef {import("./shared/ipc/channels").AskStepbitChatChannel} AskStepbitChatChannel */

/** @type {WorkspaceStateEventChannel} */
const WORKSPACE_STATE_EVENT = "quantlab:workspace-state";
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

async function unwrapInvokeResult(channel, ...args) {
  const result = await ipcRenderer.invoke(channel, ...args);
  if (!result || typeof result !== "object" || !("ok" in result)) return result;
  if (result.ok) return result.data;
  throw new Error(result.error || `IPC request failed for ${channel}.`);
}

/** @type {QuantlabDesktopBridge} */
const desktopBridge = {
  /** @returns {Promise<WorkspaceState>} */
  getWorkspaceState: () => ipcRenderer.invoke(GET_WORKSPACE_STATE_CHANNEL),
  requestJson: (relativePath) => unwrapInvokeResult(REQUEST_JSON_CHANNEL, relativePath),
  requestText: (relativePath) => unwrapInvokeResult(REQUEST_TEXT_CHANNEL, relativePath),
  getCandidatesStore: () => ipcRenderer.invoke(GET_CANDIDATES_STORE_CHANNEL),
  saveCandidatesStore: (store) => ipcRenderer.invoke(SAVE_CANDIDATES_STORE_CHANNEL, store),
  getSweepDecisionStore: () => ipcRenderer.invoke(GET_SWEEP_DECISION_STORE_CHANNEL),
  saveSweepDecisionStore: (store) => ipcRenderer.invoke(SAVE_SWEEP_DECISION_STORE_CHANNEL, store),
  getShellWorkspaceStore: () => ipcRenderer.invoke(GET_SHELL_WORKSPACE_STORE_CHANNEL),
  saveShellWorkspaceStore: (store) => ipcRenderer.invoke(SAVE_SHELL_WORKSPACE_STORE_CHANNEL, store),
  listDirectory: (targetPath, maxDepth) => ipcRenderer.invoke(LIST_DIRECTORY_CHANNEL, targetPath, maxDepth),
  readProjectText: (targetPath) => ipcRenderer.invoke(READ_PROJECT_TEXT_CHANNEL, targetPath),
  readProjectJson: (targetPath) => ipcRenderer.invoke(READ_PROJECT_JSON_CHANNEL, targetPath),
  postJson: (relativePath, payload) => unwrapInvokeResult(POST_JSON_CHANNEL, relativePath, payload),
  restartWorkspaceServer: () => ipcRenderer.invoke(RESTART_WORKSPACE_SERVER_CHANNEL),
  askStepbitChat: (payload) => ipcRenderer.invoke(ASK_STEPBIT_CHAT_CHANNEL, payload),
  openExternal: (url) => ipcRenderer.invoke(OPEN_EXTERNAL_CHANNEL, url),
  openPath: (targetPath) => ipcRenderer.invoke(OPEN_PATH_CHANNEL, targetPath),
  /**
   * @param {WorkspaceStateListener} callback
   * @returns {() => void}
   */
  onWorkspaceState: (callback) => {
    /** @param {unknown} payload */
    const wrapped = (_event, payload) => {
      const workspaceState = /** @type {WorkspaceState} */ (payload);
      callback(workspaceState);
    };
    ipcRenderer.on(WORKSPACE_STATE_EVENT, wrapped);
    return () => ipcRenderer.removeListener(WORKSPACE_STATE_EVENT, wrapped);
  },
};

contextBridge.exposeInMainWorld("quantlabDesktop", desktopBridge);
