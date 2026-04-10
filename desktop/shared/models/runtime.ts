import type { WorkspaceSource, WorkspaceStatus } from "./workspace";

export type RuntimeChipTone =
  | "up"
  | "down"
  | "warn"
  | "starting"
  | "muted"
  | "local-only"
  | "degraded"
  | "pending";

export interface RuntimeStatus {
  workspaceStatus: WorkspaceStatus;
  workspaceSource: WorkspaceSource;
  serverUrl: string | null;
  localFallbackActive: boolean;
  runsIndexed: number;
  paperSessions: number;
  brokerSessions: number;
  stepbitAppReady: boolean;
  stepbitCoreReachable: boolean;
  stepbitCoreReady: boolean;
}

export interface RuntimeChipState {
  text: string;
  tone: RuntimeChipTone;
}
