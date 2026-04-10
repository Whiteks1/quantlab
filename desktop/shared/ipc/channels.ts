export const QUANTLAB_WORKSPACE_STATE_EVENT = "quantlab:workspace-state" as const;
export const QUANTLAB_GET_WORKSPACE_STATE_CHANNEL = "quantlab:get-workspace-state" as const;

export const QUANTLAB_IPC_CHANNELS = {
  workspaceStateEvent: QUANTLAB_WORKSPACE_STATE_EVENT,
  getWorkspaceState: QUANTLAB_GET_WORKSPACE_STATE_CHANNEL,
} as const;

export type WorkspaceStateEventChannel = typeof QUANTLAB_WORKSPACE_STATE_EVENT;
export type GetWorkspaceStateChannel = typeof QUANTLAB_GET_WORKSPACE_STATE_CHANNEL;
