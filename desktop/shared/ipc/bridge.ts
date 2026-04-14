import type { WorkspaceState, WorkspaceStateListener } from "../models/workspace";

export type QuantlabJsonValue = unknown;
export type QuantlabStoreValue = unknown;
export type QuantlabChatPayload = Record<string, unknown>;
export type QuantlabChatResult = {
  content: string;
  reasoningSeen?: boolean;
} & Record<string, unknown>;
export type QuantlabPostJsonResult = {
  message?: string;
} & Record<string, unknown>;
export type QuantlabDirectoryEntry = {
  kind?: string;
  name?: string;
  path?: string;
  relative_path?: string;
  modified_at?: string;
  size_bytes?: number;
  depth?: number;
} & Record<string, unknown>;
export type QuantlabListDirectoryResult = {
  entries: QuantlabDirectoryEntry[];
  truncated?: boolean;
} & Record<string, unknown>;

export interface QuantlabDesktopBridge {
  getWorkspaceState(): Promise<WorkspaceState>;
  requestJson<T = QuantlabJsonValue>(relativePath: string): Promise<T>;
  requestText(relativePath: string): Promise<string>;
  getCandidatesStore<T = QuantlabStoreValue>(): Promise<T>;
  saveCandidatesStore<T = QuantlabStoreValue>(store: T): Promise<T>;
  getSweepDecisionStore<T = QuantlabStoreValue>(): Promise<T>;
  saveSweepDecisionStore<T = QuantlabStoreValue>(store: T): Promise<T>;
  getShellWorkspaceStore<T = QuantlabStoreValue>(): Promise<T>;
  saveShellWorkspaceStore<T = QuantlabStoreValue>(store: T): Promise<T>;
  listDirectory(targetPath: string, maxDepth?: number): Promise<QuantlabListDirectoryResult>;
  readProjectText(targetPath: string): Promise<string>;
  readProjectJson<T = QuantlabJsonValue>(targetPath: string): Promise<T>;
  postJson<T = QuantlabPostJsonResult>(relativePath: string, payload: QuantlabJsonValue): Promise<T>;
  restartWorkspaceServer(): Promise<WorkspaceState>;
  askStepbitChat<T = QuantlabChatResult>(payload: QuantlabChatPayload): Promise<T>;
  openExternal(url: string): Promise<void>;
  openPath(targetPath: string): Promise<{ ok: true }>;
  onWorkspaceState(callback: WorkspaceStateListener): () => void;
}
