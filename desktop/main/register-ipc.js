// @ts-check

function okIpcResult(data) {
  return { ok: true, data };
}

function errorIpcResult(error) {
  return {
    ok: false,
    error: error?.message || String(error || "Unknown IPC failure."),
  };
}

/**
 * @param {{
 *   ipcMain: typeof import("electron").ipcMain,
 *   shell: typeof import("electron").shell,
 *   workspace: {
 *     getState: () => import("../shared/models/workspace").WorkspaceState,
 *   },
 *   localStores: {
 *     assertPathInsideProject: (targetPath: string) => string,
 *     readCandidatesStore: () => Promise<any>,
 *     writeCandidatesStore: (store: any) => Promise<any>,
 *     readSweepDecisionStore: () => Promise<any>,
 *     writeSweepDecisionStore: (store: any) => Promise<any>,
 *     readShellWorkspaceStore: () => Promise<any>,
 *     writeShellWorkspaceStore: (store: any) => Promise<any>,
 *     listDirectoryEntries: (targetPath: string, maxDepth?: number) => Promise<any>,
 *     readProjectText: (targetPath: string) => Promise<string>,
 *     readProjectJson: (targetPath: string) => Promise<any>,
 *   },
 *   researchUi: {
 *     start: (options?: { forceRestart?: boolean }) => Promise<void>,
 *   },
 *   stepbit: {
 *     askChat: (payload: any) => Promise<any>,
 *   },
 * }} options
 */
function registerIpcHandlers({ ipcMain, shell, workspace, localStores, researchUi, stepbit }) {
  ipcMain.handle("quantlab:get-workspace-state", async () => workspace.getState());

  ipcMain.handle("quantlab:request-json", async (_event, relativePath) => {
    try {
      const workspaceState = workspace.getState();
      if (!workspaceState.serverUrl) {
        throw new Error("Research UI server is not ready yet.");
      }
      const base = workspaceState.serverUrl.replace(/\/$/, "");
      const response = await fetch(`${base}${relativePath}`);
      if (!response.ok) {
        throw new Error(`${relativePath} returned ${response.status}`);
      }
      return okIpcResult(await response.json());
    } catch (error) {
      return errorIpcResult(error);
    }
  });

  ipcMain.handle("quantlab:request-text", async (_event, relativePath) => {
    try {
      const workspaceState = workspace.getState();
      if (!workspaceState.serverUrl) {
        throw new Error("Research UI server is not ready yet.");
      }
      const base = workspaceState.serverUrl.replace(/\/$/, "");
      const response = await fetch(`${base}${relativePath}`);
      if (!response.ok) {
        throw new Error(`${relativePath} returned ${response.status}`);
      }
      return okIpcResult(await response.text());
    } catch (error) {
      return errorIpcResult(error);
    }
  });

  ipcMain.handle("quantlab:get-candidates-store", async () => localStores.readCandidatesStore());
  ipcMain.handle("quantlab:save-candidates-store", async (_event, payload) => localStores.writeCandidatesStore(payload));

  ipcMain.handle("quantlab:get-sweep-decision-store", async () => localStores.readSweepDecisionStore());
  ipcMain.handle("quantlab:save-sweep-decision-store", async (_event, payload) => localStores.writeSweepDecisionStore(payload));

  ipcMain.handle("quantlab:get-shell-workspace-store", async () => localStores.readShellWorkspaceStore());
  ipcMain.handle("quantlab:save-shell-workspace-store", async (_event, payload) => localStores.writeShellWorkspaceStore(payload));

  ipcMain.handle("quantlab:list-directory", async (_event, targetPath, maxDepth = 2) => {
    return localStores.listDirectoryEntries(targetPath, maxDepth);
  });

  ipcMain.handle("quantlab:read-project-text", async (_event, targetPath) => {
    return localStores.readProjectText(targetPath);
  });

  ipcMain.handle("quantlab:read-project-json", async (_event, targetPath) => {
    return localStores.readProjectJson(targetPath);
  });

  ipcMain.handle("quantlab:post-json", async (_event, relativePath, payload) => {
    try {
      const workspaceState = workspace.getState();
      if (!workspaceState.serverUrl) {
        throw new Error("Research UI server is not ready yet.");
      }
      const base = workspaceState.serverUrl.replace(/\/$/, "");
      const response = await fetch(`${base}${relativePath}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload ?? {}),
      });
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      if (!response.ok) {
        throw new Error(data.message || `${relativePath} returned ${response.status}`);
      }
      return okIpcResult(data);
    } catch (error) {
      return errorIpcResult(error);
    }
  });

  ipcMain.handle("quantlab:open-external", async (_event, url) => {
    await shell.openExternal(url);
  });

  ipcMain.handle("quantlab:open-path", async (_event, targetPath) => {
    const safePath = localStores.assertPathInsideProject(targetPath);
    const errorMessage = await shell.openPath(safePath);
    if (errorMessage) throw new Error(errorMessage);
    return { ok: true };
  });

  ipcMain.handle("quantlab:restart-workspace-server", async () => {
    await researchUi.start({ forceRestart: true });
    return workspace.getState();
  });

  ipcMain.handle("quantlab:ask-stepbit-chat", async (_event, payload) => {
    return stepbit.askChat(payload);
  });
}

module.exports = { registerIpcHandlers };
