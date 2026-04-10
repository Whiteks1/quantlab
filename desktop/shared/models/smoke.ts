export type SmokeMode = "fallback" | "real-path";

export interface SmokeResult {
  bridgeReady: boolean;
  shellReady: boolean;
  serverReady: boolean;
  apiReady: boolean;
  localRunsReady: boolean;
  serverUrl: string;
  error: string;
}
