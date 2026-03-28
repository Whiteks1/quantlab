const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("quantlabDesktop", {
  getWorkspaceState: () => ipcRenderer.invoke("quantlab:get-workspace-state"),
  requestJson: (relativePath) => ipcRenderer.invoke("quantlab:request-json", relativePath),
  requestText: (relativePath) => ipcRenderer.invoke("quantlab:request-text", relativePath),
  getCandidatesStore: () => ipcRenderer.invoke("quantlab:get-candidates-store"),
  saveCandidatesStore: (store) => ipcRenderer.invoke("quantlab:save-candidates-store", store),
  listDirectory: (targetPath, maxDepth) => ipcRenderer.invoke("quantlab:list-directory", targetPath, maxDepth),
  postJson: (relativePath, payload) => ipcRenderer.invoke("quantlab:post-json", relativePath, payload),
  openExternal: (url) => ipcRenderer.invoke("quantlab:open-external", url),
  openPath: (targetPath) => ipcRenderer.invoke("quantlab:open-path", targetPath),
  onWorkspaceState: (callback) => {
    const wrapped = (_event, payload) => callback(payload);
    ipcRenderer.on("quantlab:workspace-state", wrapped);
    return () => ipcRenderer.removeListener("quantlab:workspace-state", wrapped);
  },
});
