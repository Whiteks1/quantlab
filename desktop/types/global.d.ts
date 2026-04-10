import type { WorkspaceState, WorkspaceStateListener } from "../shared/models/workspace";

interface QuantlabDesktopBridge {
  getWorkspaceState(): Promise<WorkspaceState>;
  requestJson(relativePath: string): Promise<any>;
  requestText(relativePath: string): Promise<string>;
  getCandidatesStore(): Promise<any>;
  saveCandidatesStore(store: any): Promise<any>;
  getSweepDecisionStore(): Promise<any>;
  saveSweepDecisionStore(store: any): Promise<any>;
  getShellWorkspaceStore(): Promise<any>;
  saveShellWorkspaceStore(store: any): Promise<any>;
  listDirectory(targetPath: string, maxDepth?: number): Promise<any>;
  readProjectText(targetPath: string): Promise<string>;
  readProjectJson(targetPath: string): Promise<any>;
  postJson(relativePath: string, payload: any): Promise<any>;
  restartWorkspaceServer(): Promise<WorkspaceState>;
  askStepbitChat(payload: any): Promise<any>;
  openExternal(url: string): Promise<{ ok: true }>;
  openPath(targetPath: string): Promise<{ ok: true }>;
  onWorkspaceState(callback: WorkspaceStateListener): () => void;
}

declare global {
  interface Window {
    quantlabDesktop: QuantlabDesktopBridge;
  }
}

export {};
