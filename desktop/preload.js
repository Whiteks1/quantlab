const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("quantlabDesktop", {
  getWorkspaceState: () => ipcRenderer.invoke("quantlab:get-workspace-state"),
  requestJson: (relativePath) => ipcRenderer.invoke("quantlab:request-json", relativePath),
  requestText: (relativePath) => ipcRenderer.invoke("quantlab:request-text", relativePath),
  getCandidatesStore: () => ipcRenderer.invoke("quantlab:get-candidates-store"),
  saveCandidatesStore: (store) => ipcRenderer.invoke("quantlab:save-candidates-store", store),
  getSweepDecisionStore: () => ipcRenderer.invoke("quantlab:get-sweep-decision-store"),
  saveSweepDecisionStore: (store) => ipcRenderer.invoke("quantlab:save-sweep-decision-store", store),
  listDirectory: (targetPath, maxDepth) => ipcRenderer.invoke("quantlab:list-directory", targetPath, maxDepth),
  readProjectText: (targetPath) => ipcRenderer.invoke("quantlab:read-project-text", targetPath),
  readProjectJson: (targetPath) => ipcRenderer.invoke("quantlab:read-project-json", targetPath),
  postJson: (relativePath, payload) => ipcRenderer.invoke("quantlab:post-json", relativePath, payload),
  askStepbitChat: (payload) => ipcRenderer.invoke("quantlab:ask-stepbit-chat", payload),
  openExternal: (url) => ipcRenderer.invoke("quantlab:open-external", url),
  openPath: (targetPath) => ipcRenderer.invoke("quantlab:open-path", targetPath),
  onWorkspaceState: (callback) => {
    const wrapped = (_event, payload) => callback(payload);
    ipcRenderer.on("quantlab:workspace-state", wrapped);
    return () => ipcRenderer.removeListener("quantlab:workspace-state", wrapped);
  },
});
