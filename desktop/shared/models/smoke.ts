export type SmokeMode = "fallback" | "real-path";

export interface SmokeResult {
  bridgeReady: boolean;
  shellReady: boolean;
  domReady: boolean;
  workbenchReady: boolean;
  rendererMode: "legacy" | "react" | "unknown";
  serverReady: boolean;
  apiReady: boolean;
  localRunsReady: boolean;
  serverUrl: string;
  error: string;
}
