export const QUANTLAB_WORKSPACE_STATE_EVENT = "quantlab:workspace-state" as const;
export const QUANTLAB_GET_WORKSPACE_STATE_CHANNEL = "quantlab:get-workspace-state" as const;
export const QUANTLAB_REQUEST_JSON_CHANNEL = "quantlab:request-json" as const;
export const QUANTLAB_REQUEST_TEXT_CHANNEL = "quantlab:request-text" as const;
export const QUANTLAB_GET_CANDIDATES_STORE_CHANNEL = "quantlab:get-candidates-store" as const;
export const QUANTLAB_SAVE_CANDIDATES_STORE_CHANNEL = "quantlab:save-candidates-store" as const;
export const QUANTLAB_GET_SWEEP_DECISION_STORE_CHANNEL = "quantlab:get-sweep-decision-store" as const;
export const QUANTLAB_SAVE_SWEEP_DECISION_STORE_CHANNEL = "quantlab:save-sweep-decision-store" as const;
export const QUANTLAB_GET_SHELL_WORKSPACE_STORE_CHANNEL = "quantlab:get-shell-workspace-store" as const;
export const QUANTLAB_SAVE_SHELL_WORKSPACE_STORE_CHANNEL = "quantlab:save-shell-workspace-store" as const;
export const QUANTLAB_LIST_DIRECTORY_CHANNEL = "quantlab:list-directory" as const;
export const QUANTLAB_READ_PROJECT_TEXT_CHANNEL = "quantlab:read-project-text" as const;
export const QUANTLAB_READ_PROJECT_JSON_CHANNEL = "quantlab:read-project-json" as const;
export const QUANTLAB_POST_JSON_CHANNEL = "quantlab:post-json" as const;
export const QUANTLAB_OPEN_EXTERNAL_CHANNEL = "quantlab:open-external" as const;
export const QUANTLAB_OPEN_PATH_CHANNEL = "quantlab:open-path" as const;
export const QUANTLAB_RESTART_WORKSPACE_SERVER_CHANNEL = "quantlab:restart-workspace-server" as const;
export const QUANTLAB_ASK_STEPBIT_CHAT_CHANNEL = "quantlab:ask-stepbit-chat" as const;

export const QUANTLAB_IPC_CHANNELS = {
  workspaceStateEvent: QUANTLAB_WORKSPACE_STATE_EVENT,
  getWorkspaceState: QUANTLAB_GET_WORKSPACE_STATE_CHANNEL,
  requestJson: QUANTLAB_REQUEST_JSON_CHANNEL,
  requestText: QUANTLAB_REQUEST_TEXT_CHANNEL,
  getCandidatesStore: QUANTLAB_GET_CANDIDATES_STORE_CHANNEL,
  saveCandidatesStore: QUANTLAB_SAVE_CANDIDATES_STORE_CHANNEL,
  getSweepDecisionStore: QUANTLAB_GET_SWEEP_DECISION_STORE_CHANNEL,
  saveSweepDecisionStore: QUANTLAB_SAVE_SWEEP_DECISION_STORE_CHANNEL,
  getShellWorkspaceStore: QUANTLAB_GET_SHELL_WORKSPACE_STORE_CHANNEL,
  saveShellWorkspaceStore: QUANTLAB_SAVE_SHELL_WORKSPACE_STORE_CHANNEL,
  listDirectory: QUANTLAB_LIST_DIRECTORY_CHANNEL,
  readProjectText: QUANTLAB_READ_PROJECT_TEXT_CHANNEL,
  readProjectJson: QUANTLAB_READ_PROJECT_JSON_CHANNEL,
  postJson: QUANTLAB_POST_JSON_CHANNEL,
  openExternal: QUANTLAB_OPEN_EXTERNAL_CHANNEL,
  openPath: QUANTLAB_OPEN_PATH_CHANNEL,
  restartWorkspaceServer: QUANTLAB_RESTART_WORKSPACE_SERVER_CHANNEL,
  askStepbitChat: QUANTLAB_ASK_STEPBIT_CHAT_CHANNEL,
} as const;

export type WorkspaceStateEventChannel = typeof QUANTLAB_WORKSPACE_STATE_EVENT;
export type GetWorkspaceStateChannel = typeof QUANTLAB_GET_WORKSPACE_STATE_CHANNEL;
export type RequestJsonChannel = typeof QUANTLAB_REQUEST_JSON_CHANNEL;
export type RequestTextChannel = typeof QUANTLAB_REQUEST_TEXT_CHANNEL;
export type GetCandidatesStoreChannel = typeof QUANTLAB_GET_CANDIDATES_STORE_CHANNEL;
export type SaveCandidatesStoreChannel = typeof QUANTLAB_SAVE_CANDIDATES_STORE_CHANNEL;
export type GetSweepDecisionStoreChannel = typeof QUANTLAB_GET_SWEEP_DECISION_STORE_CHANNEL;
export type SaveSweepDecisionStoreChannel = typeof QUANTLAB_SAVE_SWEEP_DECISION_STORE_CHANNEL;
export type GetShellWorkspaceStoreChannel = typeof QUANTLAB_GET_SHELL_WORKSPACE_STORE_CHANNEL;
export type SaveShellWorkspaceStoreChannel = typeof QUANTLAB_SAVE_SHELL_WORKSPACE_STORE_CHANNEL;
export type ListDirectoryChannel = typeof QUANTLAB_LIST_DIRECTORY_CHANNEL;
export type ReadProjectTextChannel = typeof QUANTLAB_READ_PROJECT_TEXT_CHANNEL;
export type ReadProjectJsonChannel = typeof QUANTLAB_READ_PROJECT_JSON_CHANNEL;
export type PostJsonChannel = typeof QUANTLAB_POST_JSON_CHANNEL;
export type OpenExternalChannel = typeof QUANTLAB_OPEN_EXTERNAL_CHANNEL;
export type OpenPathChannel = typeof QUANTLAB_OPEN_PATH_CHANNEL;
export type RestartWorkspaceServerChannel = typeof QUANTLAB_RESTART_WORKSPACE_SERVER_CHANNEL;
export type AskStepbitChatChannel = typeof QUANTLAB_ASK_STEPBIT_CHAT_CHANNEL;
