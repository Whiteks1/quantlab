const { contextBridge, ipcRenderer } = require("electron");

async function unwrapInvokeResult(channel, ...args) {
  const result = await ipcRenderer.invoke(channel, ...args);
  if (!result || typeof result !== "object" || !("ok" in result)) return result;
  if (result.ok) return result.data;
  throw new Error(result.error || `IPC request failed for ${channel}.`);
}

contextBridge.exposeInMainWorld("quantlabDesktop", {
  getWorkspaceState: () => ipcRenderer.invoke("quantlab:get-workspace-state"),
  requestJson: (relativePath) => unwrapInvokeResult("quantlab:request-json", relativePath),
  requestText: (relativePath) => unwrapInvokeResult("quantlab:request-text", relativePath),
  getCandidatesStore: () => ipcRenderer.invoke("quantlab:get-candidates-store"),
  saveCandidatesStore: (store) => ipcRenderer.invoke("quantlab:save-candidates-store", store),
  getSweepDecisionStore: () => ipcRenderer.invoke("quantlab:get-sweep-decision-store"),
  saveSweepDecisionStore: (store) => ipcRenderer.invoke("quantlab:save-sweep-decision-store", store),
  getShellWorkspaceStore: () => ipcRenderer.invoke("quantlab:get-shell-workspace-store"),
  saveShellWorkspaceStore: (store) => ipcRenderer.invoke("quantlab:save-shell-workspace-store", store),
  listDirectory: (targetPath, maxDepth) => ipcRenderer.invoke("quantlab:list-directory", targetPath, maxDepth),
  readProjectText: (targetPath) => ipcRenderer.invoke("quantlab:read-project-text", targetPath),
  readProjectJson: (targetPath) => ipcRenderer.invoke("quantlab:read-project-json", targetPath),
  postJson: (relativePath, payload) => unwrapInvokeResult("quantlab:post-json", relativePath, payload),
  restartWorkspaceServer: () => ipcRenderer.invoke("quantlab:restart-workspace-server"),
  askStepbitChat: (payload) => ipcRenderer.invoke("quantlab:ask-stepbit-chat", payload),
  openExternal: (url) => ipcRenderer.invoke("quantlab:open-external", url),
  openPath: (targetPath) => ipcRenderer.invoke("quantlab:open-path", targetPath),
  onWorkspaceState: (callback) => {
    const wrapped = (_event, payload) => callback(payload);
    ipcRenderer.on("quantlab:workspace-state", wrapped);
    return () => ipcRenderer.removeListener("quantlab:workspace-state", wrapped);
  },
});
