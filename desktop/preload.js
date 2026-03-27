const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("quantlabDesktop", {
  getWorkspaceState: () => ipcRenderer.invoke("quantlab:get-workspace-state"),
  requestJson: (relativePath) => ipcRenderer.invoke("quantlab:request-json", relativePath),
  openExternal: (url) => ipcRenderer.invoke("quantlab:open-external", url),
  onWorkspaceState: (callback) => {
    const wrapped = (_event, payload) => callback(payload);
    ipcRenderer.on("quantlab:workspace-state", wrapped);
    return () => ipcRenderer.removeListener("quantlab:workspace-state", wrapped);
  },
});
