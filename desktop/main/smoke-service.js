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
      happyPathReady: false,
      happyPathRunsReady: false,
      happyPathRunDetailReady: false,
      happyPathArtifactsReady: false,
      happyPathCandidatesReady: false,
      happyPathCompareReady: false,
      happyPathRunCount: 0,
      happyPathSelectableRunCount: 0,
      serverReady: false,
      apiReady: false,
      localRunsReady: false,
      serverUrl: "",
      error: "",
      ...overrides,
    };
  }

  async function evaluateHappyPath(mainWindow) {
    const evaluation = await mainWindow.webContents.executeJavaScript(
      `(async () => {
        const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
        const waitFor = async (predicate, timeoutMs = 4500, intervalMs = 90) => {
          const deadline = Date.now() + timeoutMs;
          while (Date.now() < deadline) {
            try {
              if (predicate()) return true;
            } catch (_error) {
              // Ignore transient renderer checks.
            }
            await sleep(intervalMs);
          }
          return false;
        };
        const click = (selector) => {
          const node = document.querySelector(selector);
          if (!node) return false;
          node.dispatchEvent(new MouseEvent("click", {
            bubbles: true,
            cancelable: true,
            view: window,
          }));
          return true;
        };
        const activeTabId = () => {
          const active = document.querySelector("#tabs-bar .tab-pill.is-active");
          return active && active.dataset ? active.dataset.tabId || "" : "";
        };
        const tabContent = document.getElementById("tab-content");
        const status = {
          runs: false,
          runDetail: false,
          artifacts: false,
          candidates: false,
          compare: false,
          runCount: 0,
          selectableRunCount: 0,
          message: "",
        };
        const failures = [];

        const openedRuns = click('.nav-item[data-action="open-runs"]');
        if (openedRuns) {
          await waitFor(() => activeTabId() === "runs-native" || Boolean(tabContent && tabContent.querySelector(".runs-tab")));
        }
        status.runs = Boolean(tabContent && tabContent.querySelector(".runs-tab"));
        if (!status.runs) failures.push("runs surface missing");

        const runOpenButtons = Array.from(document.querySelectorAll("#workflow-runs-list [data-open-run]"));
        status.runCount = runOpenButtons.length;
        if (runOpenButtons.length > 0) {
          runOpenButtons[0].dispatchEvent(new MouseEvent("click", {
            bubbles: true,
            cancelable: true,
            view: window,
          }));
          await waitFor(() => activeTabId().startsWith("run:"), 5000, 100);
          await waitFor(() => {
            const placeholder = tabContent ? tabContent.querySelector(".tab-placeholder") : null;
            const text = placeholder ? String(placeholder.textContent || "") : "";
            return !placeholder || !/reading canonical run detail/i.test(text);
          }, 5000, 120);
          const runText = tabContent ? String(tabContent.textContent || "").trim() : "";
          status.runDetail = activeTabId().startsWith("run:") && Boolean(runText);
          if (!status.runDetail) failures.push("run detail unavailable");

          const openArtifactsButton = tabContent ? tabContent.querySelector("[data-open-artifacts]") : null;
          if (openArtifactsButton || runOpenButtons[0]) {
            const artifactsTrigger = openArtifactsButton || document.querySelector("#workflow-runs-list [data-open-artifacts]");
            artifactsTrigger?.dispatchEvent(new MouseEvent("click", {
              bubbles: true,
              cancelable: true,
              view: window,
            }));
            await waitFor(() => activeTabId().startsWith("artifacts:"), 5000, 100);
            await sleep(120);
          }
          const artifactText = tabContent ? String(tabContent.textContent || "").trim() : "";
          status.artifacts = activeTabId().startsWith("artifacts:") && Boolean(artifactText);
          if (!status.artifacts) failures.push("artifacts unavailable");
        } else {
          const hasExplicitEmptyState = Boolean(document.querySelector("#workflow-runs-list .empty-state"));
          status.runDetail = hasExplicitEmptyState;
          status.artifacts = hasExplicitEmptyState;
          if (!hasExplicitEmptyState) failures.push("runs empty state missing");
        }

        const openedCandidates = click('.nav-item[data-action="open-candidates"]');
        if (openedCandidates) {
          await waitFor(() => activeTabId() === "candidates");
        }
        status.candidates = activeTabId() === "candidates" && Boolean(tabContent && tabContent.textContent && tabContent.textContent.trim());
        if (!status.candidates) failures.push("candidates surface unavailable");

        const selectionInputs = Array.from(document.querySelectorAll("#workflow-runs-list input[data-select-run]"))
          .filter((node) => !node.disabled);
        status.selectableRunCount = selectionInputs.length;
        const compareButton = document.getElementById("workflow-open-compare");
        if (selectionInputs.length >= 2 && compareButton && !compareButton.disabled) {
          selectionInputs.slice(0, 2).forEach((input) => {
            if (input.checked) return;
            input.checked = true;
            input.dispatchEvent(new Event("change", { bubbles: true }));
          });
          await sleep(120);
          compareButton.dispatchEvent(new MouseEvent("click", {
            bubbles: true,
            cancelable: true,
            view: window,
          }));
          await waitFor(() => activeTabId().startsWith("compare:"), 5000, 100);
          status.compare = activeTabId().startsWith("compare:");
          if (!status.compare) failures.push("compare surface unavailable");
        } else {
          const compareDisabled = Boolean(compareButton && compareButton.disabled);
          if (compareButton && !compareButton.disabled) {
            compareButton.dispatchEvent(new MouseEvent("click", {
              bubbles: true,
              cancelable: true,
              view: window,
            }));
            await sleep(120);
          }
          const assistantMessages = Array.from(document.querySelectorAll("#chat-log .message.assistant .message-body"));
          const lastMessage = assistantMessages.length
            ? String(assistantMessages[assistantMessages.length - 1].textContent || "")
            : "";
          const compareGuarded = compareDisabled || /select 2 to 4 runs|at least two/i.test(lastMessage);
          status.compare = compareGuarded;
          if (!status.compare) failures.push("compare guard missing");
        }

        const ready = Boolean(
          status.runs
          && status.runDetail
          && status.artifacts
          && status.candidates
          && status.compare
        );
        status.message = failures.join("; ");
        return {
          ready,
          runsReady: status.runs,
          runDetailReady: status.runDetail,
          artifactsReady: status.artifacts,
          candidatesReady: status.candidates,
          compareReady: status.compare,
          runCount: status.runCount,
          selectableRunCount: status.selectableRunCount,
          message: status.message,
        };
      })()`,
      true,
    );
    return {
      happyPathReady: Boolean(evaluation?.ready),
      happyPathRunsReady: Boolean(evaluation?.runsReady),
      happyPathRunDetailReady: Boolean(evaluation?.runDetailReady),
      happyPathArtifactsReady: Boolean(evaluation?.artifactsReady),
      happyPathCandidatesReady: Boolean(evaluation?.candidatesReady),
      happyPathCompareReady: Boolean(evaluation?.compareReady),
      happyPathRunCount: Number(evaluation?.runCount || 0),
      happyPathSelectableRunCount: Number(evaluation?.selectableRunCount || 0),
      happyPathMessage: String(evaluation?.message || "").trim(),
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
      const happyPath = await evaluateHappyPath(mainWindow);
      result.happyPathReady = happyPath.happyPathReady;
      result.happyPathRunsReady = happyPath.happyPathRunsReady;
      result.happyPathRunDetailReady = happyPath.happyPathRunDetailReady;
      result.happyPathArtifactsReady = happyPath.happyPathArtifactsReady;
      result.happyPathCandidatesReady = happyPath.happyPathCandidatesReady;
      result.happyPathCompareReady = happyPath.happyPathCompareReady;
      result.happyPathRunCount = happyPath.happyPathRunCount;
      result.happyPathSelectableRunCount = happyPath.happyPathSelectableRunCount;
      result.shellReady = result.bridgeReady && result.domReady && result.workbenchReady && result.happyPathReady && (
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
      if (!result.happyPathReady) {
        result.error = result.error
          || `desktop happy-path check failed (runs=${result.happyPathRunsReady}, runDetail=${result.happyPathRunDetailReady}, artifacts=${result.happyPathArtifactsReady}, candidates=${result.happyPathCandidatesReady}, compare=${result.happyPathCompareReady}, runCount=${result.happyPathRunCount}, selectableRuns=${result.happyPathSelectableRunCount})`
          + `${happyPath.happyPathMessage ? `: ${happyPath.happyPathMessage}` : ""}`;
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
