// @ts-check

/** @typedef {import("../shared/models/smoke").SmokeResult} SmokeResult */

/**
 * @param {{
 *   app: typeof import("electron").app,
 *   fsp: typeof import("fs/promises"),
 *   path: typeof import("path"),
 *   smokeOutputPath: string,
 *   smokeMode: "fallback" | "real-path",
 *   startupTimeoutMs: number,
 *   outputsRoot: string,
 *   workspace: { getState: () => import("../shared/models/workspace").WorkspaceState },
 *   researchUi: { isReachable: (baseUrl: string) => Promise<boolean> },
 *   localStores: {
 *     readJsonFile: (targetPath: string) => Promise<any>,
 *     readProjectJson: (targetPath: string) => Promise<any>,
 *   },
 *   getMainWindow: () => import("electron").BrowserWindow | null,
 * }} options
 */
function createSmokeService({
  app,
  fsp,
  path,
  smokeOutputPath,
  smokeMode,
  startupTimeoutMs,
  outputsRoot,
  workspace,
  researchUi,
  localStores,
  getMainWindow,
}) {
  let smokeResultPersisted = false;
  let smokeDidFinishLoadSeen = false;

  /**
   * @param {Partial<SmokeResult>} [overrides]
   * @returns {SmokeResult}
   */
  function defaultResult(overrides = {}) {
    return {
      bridgeReady: false,
      shellReady: false,
      domReady: false,
      workbenchReady: false,
      rendererMode: "unknown",
      serverReady: false,
      apiReady: false,
      localRunsReady: false,
      serverUrl: "",
      error: "",
      ...overrides,
    };
  }

  /**
   * @param {Partial<SmokeResult>} [resultOverrides]
   */
  async function persistResult(resultOverrides = {}) {
    if (!smokeOutputPath || smokeResultPersisted) return;
    const result = defaultResult(resultOverrides);
    await fsp.mkdir(path.dirname(smokeOutputPath), { recursive: true });
    await fsp.writeFile(smokeOutputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
    smokeResultPersisted = true;
  }

  /**
   * @param {string} errorMessage
   * @param {Partial<SmokeResult>} [overrides]
   */
  async function failAndQuit(errorMessage, overrides = {}) {
    try {
      await persistResult({
        error: errorMessage,
        ...overrides,
      });
    } catch (_error) {
      // Best effort persistence; the outer smoke harness also handles missing files.
    } finally {
      process.exitCode = 1;
      app.quit();
    }
  }

  async function run() {
    const mainWindow = getMainWindow();
    if (!mainWindow || mainWindow.isDestroyed()) {
      await failAndQuit("Desktop smoke window was not available when smoke started.");
      return;
    }

    /** @type {SmokeResult} */
    const result = defaultResult();
    try {
      result.bridgeReady = await mainWindow.webContents.executeJavaScript(
        "Boolean(window.quantlabDesktop && typeof window.quantlabDesktop.getWorkspaceState === 'function')",
        true,
      );
      const uiDeadline = Date.now() + 5000;
      while (Date.now() < uiDeadline) {
        const uiState = await mainWindow.webContents.executeJavaScript(
          `(() => {
            const shellState = window.__quantlab?.getShellState?.() || {};
            const rendererMode = shellState.rendererMode || window.__quantlab?.rendererMode || "unknown";
            const legacyShell = document.getElementById("legacy-shell");
            const tabContent = document.getElementById("tab-content");
            const tabsBar = document.getElementById("tabs-bar");
            const workspaceGrid = document.querySelector(".workspace-grid");
            const legacyVisible = Boolean(
              legacyShell
              && !legacyShell.classList.contains("hidden")
              && getComputedStyle(legacyShell).display !== "none"
            );
            const domReady = Boolean(document.body && (legacyShell || document.getElementById("react-root")));
            const workbenchReady = rendererMode === "legacy"
              ? Boolean(legacyVisible && tabContent && tabsBar && workspaceGrid)
              : Boolean(document.getElementById("react-root"));
            return {
              rendererMode,
              domReady,
              workbenchReady,
            };
          })()`,
          true,
        );
        result.rendererMode = uiState?.rendererMode || "unknown";
        result.domReady = Boolean(uiState?.domReady);
        result.workbenchReady = Boolean(uiState?.workbenchReady);
        if (result.domReady && result.workbenchReady) break;
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
      const deadline = Date.now() + startupTimeoutMs;
      while (Date.now() < deadline) {
        const workspaceState = workspace.getState();
        if (workspaceState.serverUrl && await researchUi.isReachable(workspaceState.serverUrl)) {
          result.serverReady = true;
          result.apiReady = true;
          result.serverUrl = workspaceState.serverUrl;
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 250));
      }
      try {
        const localRuns = process.env.QUANTLAB_DESKTOP_SMOKE === "1"
          ? await localStores.readJsonFile(path.join(outputsRoot, "runs", "runs_index.json"))
          : await localStores.readProjectJson("outputs/runs/runs_index.json");
        result.localRunsReady = Array.isArray(localRuns?.runs);
      } catch (_error) {
        result.localRunsReady = false;
      }
      result.shellReady = result.bridgeReady && result.domReady && result.workbenchReady && (
        smokeMode === "real-path"
          ? result.serverReady
          : (result.serverReady || result.localRunsReady)
      );
      if (!result.serverReady) {
        result.error = workspace.getState().error || (
          smokeMode === "real-path"
            ? "research_ui did not become reachable during real-path smoke run."
            : (result.localRunsReady
                ? "research_ui did not become reachable, but the shell loaded via the local runs index."
                : "research_ui did not become reachable during smoke run.")
        );
      }
      if (!result.domReady || !result.workbenchReady) {
        result.error = `desktop renderer safety check failed: renderer=${result.rendererMode}, domReady=${result.domReady}, workbenchReady=${result.workbenchReady}`;
      }
    } catch (error) {
      result.error = error.message;
    }

    await persistResult(result);

    if (!result.bridgeReady || !result.shellReady) {
      process.exitCode = 1;
    }
    app.quit();
  }

  function markDidFinishLoadSeen() {
    smokeDidFinishLoadSeen = true;
  }

  function hasPersistedResult() {
    return smokeResultPersisted;
  }

  function didFinishLoad() {
    return smokeDidFinishLoadSeen;
  }

  return {
    defaultResult,
    persistResult,
    failAndQuit,
    run,
    markDidFinishLoadSeen,
    hasPersistedResult,
    didFinishLoad,
  };
}

module.exports = { createSmokeService };
