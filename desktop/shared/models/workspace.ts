export type WorkspaceStatus = "idle" | "starting" | "ready" | "stopped" | "error";

export type WorkspaceSource = "managed" | "external" | null;

export interface WorkspaceState {
  status: WorkspaceStatus;
  serverUrl: string | null;
  logs: string[];
  error: string | null;
  source: WorkspaceSource;
}

export type WorkspaceStatePatch = Partial<WorkspaceState>;

export type WorkspaceStateListener = (state: WorkspaceState) => void;
