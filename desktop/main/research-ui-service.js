// @ts-nocheck -- legacy JS file, not migrated to strict TypeScript. See #462.

/**
 * @param {{
 *   fs: typeof import("fs"),
 *   path: typeof import("path"),
 *   spawn: typeof import("child_process").spawn,
 *   projectRoot: string,
 *   serverScript: string,
 *   researchUiUrls: string[],
 *   healthPath: string,
 *   startupTimeoutMs: number,
 *   workspace: {
 *     getState: () => import("../shared/models/workspace").WorkspaceState,
 *     update: (patch: import("../shared/models/workspace").WorkspaceStatePatch) => void,
 *     appendLog: (line: string) => void,
 *   },
 * }} options
 */
function createResearchUiService({
  fs,
  path,
  spawn,
  projectRoot,
  serverScript,
  researchUiUrls,
  healthPath,
  startupTimeoutMs,
  workspace,
}) {
  /** @type {import("child_process").ChildProcessWithoutNullStreams | null} */
  let researchServerProcess = null;
  let researchServerOwned = false;
  /** @type {NodeJS.Timeout | null} */
  let researchStartupTimer = null;

  function clearStartupTimer() {
    if (researchStartupTimer) {
      clearTimeout(researchStartupTimer);
      researchStartupTimer = null;
    }
  }

  function scheduleStartupTimeout() {
    clearStartupTimer();
    researchStartupTimer = setTimeout(() => {
      if (workspace.getState().status === "ready") return;
      workspace.update({
        status: "error",
        error: "research_ui did not become ready before the startup timeout.",
      });
      workspace.appendLog("[startup-timeout] research_ui did not become ready before the timeout.");
    }, startupTimeoutMs);
  }

  async function isReachable(baseUrl) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1000);
    try {
      const response = await fetch(`${String(baseUrl).replace(/\/$/, "")}${healthPath}`, {
        signal: controller.signal,
        headers: { "User-Agent": "QuantLab-Desktop" },
      });
      return response.ok;
    } catch (_error) {
      return false;
    } finally {
      clearTimeout(timeout);
    }
  }

  async function detectServerUrl() {
    for (const candidate of researchUiUrls) {
      if (await isReachable(candidate)) return candidate;
    }
    return "";
  }

  function markReady(discoveredUrl, source) {
    clearStartupTimer();
    workspace.update({
      status: "ready",
      serverUrl: discoveredUrl,
      error: null,
      source,
    });
  }

  async function monitorStartup() {
    const deadline = Date.now() + startupTimeoutMs;
    while (researchServerProcess && Date.now() < deadline) {
      const discoveredUrl = await detectServerUrl();
      if (discoveredUrl) {
        markReady(discoveredUrl, researchServerOwned ? "managed" : "external");
        workspace.appendLog(`[startup] research_ui reachable at ${discoveredUrl}`);
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }

  function resolvePythonCandidates() {
    const isWindows = process.platform === "win32";
    const localVenv = path.join(projectRoot, ".venv", isWindows ? "Scripts" : "bin", isWindows ? "python.exe" : "python");
    const candidates = [
      localVenv,
      process.env.PYTHON || "",
      isWindows ? "python" : "python3",
    ]
      .map((value) => String(value || "").trim())
      .filter(Boolean);

    return [...new Set(candidates)].filter((candidate) => {
      if (!path.isAbsolute(candidate)) return true;
      try {
        fs.accessSync(candidate, fs.constants.R_OK);
        return true;
      } catch (_error) {
        return false;
      }
    });
  }

  function extractServerUrl(line) {
    const match = String(line).match(/URL:\s*(http:\/\/[^\s]+)/i);
    return match ? match[1] : null;
  }

  /**
   * @param {import("child_process").ChildProcessWithoutNullStreams} processHandle
   * @param {string} pythonCommand
   * @param {string[]} candidates
   * @param {number} candidateIndex
   */
  function bindProcess(processHandle, pythonCommand, candidates, candidateIndex) {
    researchServerProcess = processHandle;
    researchServerOwned = true;

    processHandle.stdout.setEncoding("utf8");
    processHandle.stderr.setEncoding("utf8");
    monitorStartup().catch((error) => {
      workspace.appendLog(`[startup-monitor-error] ${error.message}`);
    });

    processHandle.stdout.on("data", (chunk) => {
      String(chunk || "")
        .split(/\r?\n/)
        .forEach((line) => {
          if (!line.trim()) return;
          workspace.appendLog(line);
          const discoveredUrl = extractServerUrl(line);
          if (discoveredUrl) {
            isReachable(discoveredUrl)
              .then((reachable) => {
                if (!reachable || !researchServerProcess || researchServerProcess !== processHandle) return;
                markReady(discoveredUrl, "managed");
              })
              .catch(() => {});
          }
        });
    });

    processHandle.stderr.on("data", (chunk) => {
      String(chunk || "")
        .split(/\r?\n/)
        .forEach((line) => {
          if (!line.trim()) return;
          workspace.appendLog(`[stderr] ${line}`);
        });
    });

    processHandle.on("exit", (code, signal) => {
      if (researchServerProcess !== processHandle) return;
      researchServerProcess = null;
      researchServerOwned = false;
      clearStartupTimer();
      workspace.update({
        status: "stopped",
        serverUrl: null,
        error: code === 0 ? null : `research_ui exited (${code ?? "null"}${signal ? `, ${signal}` : ""})`,
        source: "managed",
      });
    });

    processHandle.on("error", (error) => {
      if (researchServerProcess === processHandle) {
        researchServerProcess = null;
        researchServerOwned = false;
      }
      const processError = /** @type {NodeJS.ErrnoException} */ (error);
      const shouldRetry =
        ["EACCES", "EPERM", "ENOENT"].includes(processError?.code || "")
        && candidateIndex < candidates.length - 1;
      if (shouldRetry) {
        const nextCommand = candidates[candidateIndex + 1];
        workspace.appendLog(`[spawn-error] ${pythonCommand} failed (${processError.code}). Retrying with ${nextCommand}.`);
        launchProcess(candidates, candidateIndex + 1);
        return;
      }
      clearStartupTimer();
      workspace.update({
        status: "error",
        serverUrl: null,
        error: error.message,
        source: "managed",
      });
      workspace.appendLog(`[spawn-error] ${error.message}`);
    });
  }

  function launchProcess(candidates, candidateIndex = 0) {
    const pythonCommand = candidates[candidateIndex];
    workspace.appendLog(`[startup] launching research_ui with ${pythonCommand}`);
    const child = spawn(pythonCommand, [serverScript], {
      cwd: projectRoot,
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"],
    });
    bindProcess(child, pythonCommand, candidates, candidateIndex);
  }

  async function start({ forceRestart = false } = {}) {
    if (forceRestart) {
      stop({ force: true });
    }

    if (researchServerProcess) return;

    const existingUrl = await detectServerUrl();
    if (existingUrl) {
      researchServerOwned = false;
      markReady(existingUrl, "external");
      workspace.appendLog(`[startup] reusing existing research_ui server at ${existingUrl}`);
      return;
    }

    workspace.update({
      status: "starting",
      serverUrl: null,
      error: null,
      source: "managed",
    });
    scheduleStartupTimeout();

    const pythonCandidates = resolvePythonCandidates();
    if (!pythonCandidates.length) {
      clearStartupTimer();
      workspace.update({
        status: "error",
        serverUrl: null,
        error: "No usable Python interpreter was found for research_ui startup.",
        source: "managed",
      });
      return;
    }

    launchProcess(pythonCandidates, 0);
  }

  function stop({ force = false } = {}) {
    clearStartupTimer();
    if (!researchServerProcess || !researchServerOwned) return;
    try {
      if (process.platform === "win32" && researchServerProcess.pid) {
        spawn("taskkill", ["/PID", String(researchServerProcess.pid), "/T", "/F"], {
          windowsHide: true,
          stdio: "ignore",
        });
      } else {
        researchServerProcess.kill(force ? "SIGKILL" : "SIGTERM");
      }
    } catch (_error) {
      // Best effort shutdown.
    }
    researchServerProcess = null;
    researchServerOwned = false;
  }

  return {
    getProcess: () => researchServerProcess,
    isOwned: () => researchServerOwned,
    isReachable,
    detectServerUrl,
    start,
    stop,
  };
}

module.exports = { createResearchUiService };
