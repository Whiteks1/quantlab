// @ts-nocheck -- legacy JS file, not migrated to strict TypeScript. See #462.

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
      parityGateName: "react-parity-v1",
      parityGatePassed: false,
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
      happyPathSystemReady: false,
      happyPathExperimentsReady: false,
      happyPathPaperOpsReady: false,
      happyPathAssistantReady: false,
      happyPathLaunchReady: false,
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
        const getTabContent = () => document.getElementById("tab-content");
        const rendererMode = window.__quantlab?.getShellState?.()?.rendererMode || window.__quantlab?.rendererMode || "unknown";
        const status = {
          runs: false,
          runDetail: false,
          artifacts: false,
          candidates: false,
          compare: false,
          system: rendererMode !== "react",
          experiments: rendererMode !== "react",
          paperOps: rendererMode !== "react",
          assistant: rendererMode !== "react",
          launch: rendererMode !== "react",
          runCount: 0,
          selectableRunCount: 0,
          message: "",
        };
        const failures = [];
        const validateReactSurface = async (action, expectedTabId, selector, label, allowPlaceholder = false) => {
          const clicked = click('.nav-item[data-action="' + action + '"]');
          if (!clicked) {
            failures.push(label + " nav unavailable");
            return false;
          }
          await waitFor(() => activeTabId() === expectedTabId, 5000, 100);
          const tabMatches = activeTabId() === expectedTabId;
          const hasSurface = Boolean(document.querySelector(selector));
          const hasPlaceholder = Boolean(getTabContent()?.querySelector(".tab-placeholder"));
          const ok = tabMatches && hasSurface && (allowPlaceholder || !hasPlaceholder);
          if (!ok) {
            failures.push(label + " surface unavailable");
          }
          return ok;
        };

        const openedRuns = click('.nav-item[data-action="open-runs"]');
        if (openedRuns) {
          await waitFor(() => activeTabId() === "runs-native" || Boolean(getTabContent() && getTabContent().querySelector(".runs-tab")));
        }
        status.runs = Boolean(document.querySelector(".runs-tab"));
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
            const placeholder = document.querySelector(".tab-placeholder");
            const text = placeholder ? String(placeholder.textContent || "") : "";
            return !placeholder || !/reading canonical run detail/i.test(text);
          }, 5000, 120);
          const runText = document.body ? String(document.body.textContent || "").trim() : "";
          const rawActiveId = activeTabId();
          status.runDetail = rawActiveId.startsWith("run:") && Boolean(document.querySelector(".run-detail-shell"));
          if (!status.runDetail) {
            const hasTabsBar = Boolean(document.getElementById("tabs-bar"));
            const html = document.body.innerHTML.slice(0, 500);
            failures.push('run detail unavailable (activeId="' + rawActiveId + '", hasTabsBar=' + hasTabsBar + ', hasShell=' + Boolean(document.querySelector(".run-detail-shell")) + ')');
          }

          const openArtifactsButton = document.querySelector("[data-open-artifacts]");
          if (openArtifactsButton || runOpenButtons[0]) {
            const artifactsTrigger = openArtifactsButton || document.querySelector("#workflow-runs-list [data-open-artifacts]");
            artifactsTrigger?.dispatchEvent(new MouseEvent("click", {
              bubbles: true,
              cancelable: true,
              view: window,
            }));
            // In the consolidated view, artifacts are in the run detail tab.
            // We wait for the artifact explorer section to be visible.
            await waitFor(() => Boolean(document.querySelector(".artifact-list")), 5000, 100);
            await sleep(120);
          }
          const artifactText = document.body ? String(document.body.textContent || "").trim() : "";
          const hasArtifactList = Boolean(document.querySelector(".artifact-list"));
          status.artifacts = (activeTabId().startsWith("artifacts:") || (activeTabId().startsWith("run:") && hasArtifactList)) && Boolean(artifactText);
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
        status.candidates = activeTabId() === "candidates" && Boolean(document.querySelector(".candidates-shell") || document.querySelector(".candidates-tab"));
        if (!status.candidates) failures.push("candidates surface unavailable");

        if (rendererMode === "react") {
          click('.nav-item[data-action="open-runs"]');
          await waitFor(() => activeTabId() === "runs-native" || Boolean(document.querySelector(".runs-tab")), 5000, 100);
        }

        const selectionInputs = Array.from(document.querySelectorAll("#workflow-runs-list input[data-select-run]"))
          .filter((node) => !node.disabled);
        status.selectableRunCount = selectionInputs.length;
        const compareButton = document.getElementById("workflow-open-compare");
        const compareNavButton = document.querySelector('.nav-item[data-action="open-compare"]');
        if (selectionInputs.length >= 2 && (rendererMode === "react" ? compareNavButton : (compareButton && !compareButton.disabled))) {
          selectionInputs.slice(0, 2).forEach((input) => {
            if (input.checked) return;
            if (rendererMode === "react") {
              input.dispatchEvent(new MouseEvent("click", {
                bubbles: true,
                cancelable: true,
                view: window,
              }));
            } else {
              input.checked = true;
              input.dispatchEvent(new Event("change", { bubbles: true }));
            }
          });
          await waitFor(() => Array.from(document.querySelectorAll("#workflow-runs-list input[data-select-run]")).filter((input) => input.checked).length >= 2, 2000, 100);
          const compareTrigger = rendererMode === "react" ? compareNavButton : compareButton;
          compareTrigger.dispatchEvent(new MouseEvent("click", {
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

        if (rendererMode === "react") {
          status.system = await validateReactSurface("open-system", "system", ".system-pane", "system");
          status.experiments = await validateReactSurface("open-experiments", "experiments", ".experiments-pane", "experiments");
          status.paperOps = await validateReactSurface("open-paper-ops", "paper-ops", ".paper-ops-pane", "paper ops");
          status.assistant = await validateReactSurface("open-assistant", "assistant", ".assistant-pane", "assistant", true);
          status.launch = await validateReactSurface("open-launch", "launch", ".launch-pane", "launch");
          click('.nav-item[data-action="open-runs"]');
          await waitFor(() => activeTabId() === "runs-native" || Boolean(document.querySelector(".runs-tab")), 5000, 100);
        }

        const ready = Boolean(
          status.runs
          && status.runDetail
          && status.artifacts
          && status.candidates
          && status.compare
          && status.system
          && status.experiments
          && status.paperOps
          && status.assistant
          && status.launch
        );
        status.message = failures.join("; ");
        return {
          ready,
          runsReady: status.runs,
          runDetailReady: status.runDetail,
          artifactsReady: status.artifacts,
          candidatesReady: status.candidates,
          compareReady: status.compare,
          systemReady: status.system,
          experimentsReady: status.experiments,
          paperOpsReady: status.paperOps,
          assistantReady: status.assistant,
          launchReady: status.launch,
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
      happyPathSystemReady: Boolean(evaluation?.systemReady),
      happyPathExperimentsReady: Boolean(evaluation?.experimentsReady),
      happyPathPaperOpsReady: Boolean(evaluation?.paperOpsReady),
      happyPathAssistantReady: Boolean(evaluation?.assistantReady),
      happyPathLaunchReady: Boolean(evaluation?.launchReady),
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
            const reactRoot = document.getElementById("react-root");
            const reactShell = document.querySelector('[data-smoke="react-shell"]');
            const tabContent = document.getElementById("tab-content");
            const tabsBar = document.getElementById("tabs-bar");
            const workspaceGrid = document.querySelector(".workspace-grid");
            const legacyVisible = Boolean(
              legacyShell
              && !legacyShell.classList.contains("hidden")
              && getComputedStyle(legacyShell).display !== "none"
            );
            const domReady = Boolean(document.body && (legacyShell || reactRoot));
            const workbenchReady = rendererMode === "legacy"
              ? Boolean(legacyVisible && tabContent && tabsBar && workspaceGrid)
              : Boolean(reactRoot && reactShell && tabContent && tabsBar);
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
      result.happyPathSystemReady = happyPath.happyPathSystemReady;
      result.happyPathExperimentsReady = happyPath.happyPathExperimentsReady;
      result.happyPathPaperOpsReady = happyPath.happyPathPaperOpsReady;
      result.happyPathAssistantReady = happyPath.happyPathAssistantReady;
      result.happyPathLaunchReady = happyPath.happyPathLaunchReady;
      result.happyPathRunCount = happyPath.happyPathRunCount;
      result.happyPathSelectableRunCount = happyPath.happyPathSelectableRunCount;
      result.parityGatePassed = result.happyPathReady;
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
        const happyPathError = `desktop happy-path check failed (runs=${result.happyPathRunsReady}, runDetail=${result.happyPathRunDetailReady}, artifacts=${result.happyPathArtifactsReady}, candidates=${result.happyPathCandidatesReady}, compare=${result.happyPathCompareReady}, system=${result.happyPathSystemReady}, experiments=${result.happyPathExperimentsReady}, paperOps=${result.happyPathPaperOpsReady}, assistant=${result.happyPathAssistantReady}, launch=${result.happyPathLaunchReady}, runCount=${result.happyPathRunCount}, selectableRuns=${result.happyPathSelectableRunCount})${happyPath.happyPathMessage ? `: ${happyPath.happyPathMessage}` : ""}`;
        result.error = result.error ? `${result.error} | ${happyPathError}` : happyPathError;
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
