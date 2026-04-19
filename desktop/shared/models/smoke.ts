export type SmokeMode = "fallback" | "real-path";

export interface SmokeResult {
  bridgeReady: boolean;
  shellReady: boolean;
  domReady: boolean;
  workbenchReady: boolean;
  rendererMode: "legacy" | "react" | "unknown";
  happyPathReady: boolean;
  happyPathRunsReady: boolean;
  happyPathRunDetailReady: boolean;
  happyPathArtifactsReady: boolean;
  happyPathCandidatesReady: boolean;
  happyPathCompareReady: boolean;
  happyPathRunCount: number;
  happyPathSelectableRunCount: number;
  serverReady: boolean;
  apiReady: boolean;
  localRunsReady: boolean;
  serverUrl: string;
  error: string;
}
