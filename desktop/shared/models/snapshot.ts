export type SnapshotStatusValue = "idle" | "ok" | "degraded" | "error";

export type SnapshotSource = "api" | "local" | "none";

export interface SnapshotStatus {
  status: SnapshotStatusValue;
  error: string | null;
  source: SnapshotSource;
  lastSuccessAt: string | null;
  consecutiveErrors: number;
  refreshPaused: boolean;
}
