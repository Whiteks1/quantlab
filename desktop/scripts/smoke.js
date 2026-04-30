const fs = require("fs/promises");
const os = require("os");
const path = require("path");
const { spawn } = require("child_process");

/** @typedef {import("../shared/models/smoke").SmokeMode} SmokeMode */
/** @typedef {import("../shared/models/smoke").SmokeResult} SmokeResult */

function parseSmokeRenderer(argv) {
  const rawRenderer = argv
    .map((entry) => String(entry || "").trim())
    .find((entry) => entry.startsWith("--renderer="))
    ?.slice("--renderer=".length);
  if (!rawRenderer || rawRenderer === "legacy" || rawRenderer === "react") {
    return rawRenderer || "legacy";
  }
  throw new Error(`Unsupported desktop smoke renderer: ${rawRenderer}`);
}

function parseSmokeMode(argv) {
  const rawMode = argv
    .map((entry) => String(entry || "").trim())
    .find((entry) => entry.startsWith("--mode="))
    ?.slice("--mode=".length);
  if (!rawMode || rawMode === "fallback" || rawMode === "real-path") {
    return /** @type {SmokeMode} */ (rawMode || "fallback");
  }
  throw new Error(`Unsupported desktop smoke mode: ${rawMode}`);
}

async function main() {
  const argv = process.argv.slice(2);
  const mode = parseSmokeMode(argv);
  const renderer = parseSmokeRenderer(argv);
  const desktopRoot = path.resolve(__dirname, "..");
  const electronBinary = require("electron");
  const electronArgs = process.platform === "linux" ? ["--no-sandbox", "."] : ["."];
  const tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "quantlab-desktop-smoke-"));
  const outputPath = path.join(tempRoot, "result.json");
  const desktopOutputsRoot = path.join(tempRoot, "outputs");
  const workspaceStatePath = path.join(desktopOutputsRoot, "desktop", "workspace_state.json");
  const smokeRunsDir = path.join(desktopOutputsRoot, "runs");
  const smokeRunsIndexPath = path.join(smokeRunsDir, "runs_index.json");
  const smokeRunOneId = "smoke_run_001";
  const smokeRunTwoId = "smoke_run_002";
  const smokeRunOnePath = path.join(smokeRunsDir, smokeRunOneId);
  const smokeRunTwoPath = path.join(smokeRunsDir, smokeRunTwoId);
  const nowIso = new Date().toISOString();
  let seededRunsIndex = false;

  await fs.mkdir(path.dirname(workspaceStatePath), { recursive: true });
  await fs.writeFile(
    workspaceStatePath,
    `${JSON.stringify({
      version: 1,
      updated_at: null,
      active_tab_id: "paper-ops",
      selected_run_ids: [],
      tabs: [
        {
          id: "paper-ops",
          kind: "paper",
          navKind: "ops",
          title: "Paper Ops",
        },
      ],
      launch_form: {
        command: "run",
        ticker: "",
        start: "",
        end: "",
        interval: "",
        cash: "",
        paper: false,
        config_path: "",
        out_dir: "",
      },
    }, null, 2)}\n`,
    "utf8",
  );

  try {
    await fs.access(smokeRunsIndexPath);
  } catch (_error) {
    await fs.mkdir(smokeRunsDir, { recursive: true });
    await fs.mkdir(smokeRunOnePath, { recursive: true });
    await fs.mkdir(smokeRunTwoPath, { recursive: true });
    const smokeReportOne = {
      generated_at: nowIso,
      summary: {
        run_id: smokeRunOneId,
        mode: "grid",
        ticker: "ETH-USD",
        total_return: 0.12,
        sharpe_simple: 1.1,
        max_drawdown: -0.08,
        trades: 4,
      },
      config_resolved: {
        ticker: "ETH-USD",
        start: "2024-01-01",
        end: "2024-03-31",
        interval: "1d",
      },
      results: [],
    };
    const smokeReportTwo = {
      generated_at: nowIso,
      summary: {
        run_id: smokeRunTwoId,
        mode: "walkforward",
        ticker: "BTC-USD",
        total_return: 0.09,
        sharpe_simple: 0.8,
        max_drawdown: -0.11,
        trades: 6,
      },
      config_resolved: {
        ticker: "BTC-USD",
        start: "2024-01-01",
        end: "2024-03-31",
        interval: "1d",
      },
      results: [],
    };
    await fs.writeFile(path.join(smokeRunOnePath, "report.json"), `${JSON.stringify(smokeReportOne, null, 2)}\n`, "utf8");
    await fs.writeFile(path.join(smokeRunTwoPath, "report.json"), `${JSON.stringify(smokeReportTwo, null, 2)}\n`, "utf8");
    await fs.writeFile(path.join(smokeRunOnePath, "notes.txt"), "smoke artifact\n", "utf8");
    await fs.writeFile(path.join(smokeRunTwoPath, "notes.txt"), "smoke artifact\n", "utf8");
    await fs.writeFile(
      smokeRunsIndexPath,
      `${JSON.stringify({
        updated_at: nowIso,
        runs: [
          {
            run_id: smokeRunOneId,
            mode: "grid",
            ticker: "ETH-USD",
            created_at: nowIso,
            git_commit: "smoke000",
            total_return: 0.12,
            sharpe_simple: 1.1,
            max_drawdown: -0.08,
            trades: 4,
            path: smokeRunOnePath,
          },
          {
            run_id: smokeRunTwoId,
            mode: "walkforward",
            ticker: "BTC-USD",
            created_at: nowIso,
            git_commit: "smoke001",
            total_return: 0.09,
            sharpe_simple: 0.8,
            max_drawdown: -0.11,
            trades: 6,
            path: smokeRunTwoPath,
          },
        ],
      }, null, 2)}\n`,
      "utf8",
    );
    seededRunsIndex = true;
  }

  try {
    const child = spawn(electronBinary, electronArgs, {
      cwd: desktopRoot,
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"],
      env: {
        ...process.env,
        QUANTLAB_DESKTOP_SMOKE: "1",
        QUANTLAB_DESKTOP_SMOKE_MODE: mode,
        QUANTLAB_DESKTOP_SMOKE_OUTPUT: outputPath,
        QUANTLAB_DESKTOP_OUTPUTS_ROOT: desktopOutputsRoot,
        QUANTLAB_DESKTOP_RENDERER: renderer,
        ...(mode === "fallback" ? { QUANTLAB_DESKTOP_DISABLE_SERVER_BOOT: "1" } : {}),
      },
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += String(chunk || "");
    });
    child.stderr.on("data", (chunk) => {
      stderr += String(chunk || "");
    });

    const timeout = setTimeout(() => {
      child.kill();
    }, 45000);

    const exitCode = await new Promise((resolve, reject) => {
      child.on("error", reject);
      child.on("exit", (code) => resolve(code ?? 1));
    });
    clearTimeout(timeout);
    /** @type {SmokeResult | null} */
    let result = null;
    for (let attempt = 0; attempt < 10; attempt += 1) {
      try {
        const raw = await fs.readFile(outputPath, "utf8");
        if (!raw.trim()) {
          throw new SyntaxError("Desktop smoke result.json is still empty.");
        }
        result = /** @type {SmokeResult} */ (JSON.parse(raw));
        break;
      } catch (error) {
        const incompleteJson = error instanceof SyntaxError;
        if (error?.code !== "ENOENT" && !incompleteJson) throw error;
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
    }
    if (!result) {
      throw new Error(
        `Desktop smoke did not persist result.json before Electron exited (code ${exitCode}).`
        + `${stdout.trim() ? ` stdout: ${stdout.trim()}` : ""}`
        + `${stderr.trim() ? ` stderr: ${stderr.trim()}` : ""}`,
      );
    }

    const passed =
      mode === "real-path"
        ? (
          exitCode === 0
          && result.bridgeReady
          && result.domReady
          && result.workbenchReady
          && result.happyPathReady
          && (renderer !== "react" || Boolean(
            result.parityGatePassed
            && result.happyPathSystemReady
            && result.happyPathExperimentsReady
            && result.happyPathPaperOpsReady
            && result.happyPathAssistantReady
            && result.happyPathLaunchReady
          ))
          && result.serverReady
          && result.apiReady
        )
        : (
          exitCode === 0
          && result.bridgeReady
          && result.domReady
          && result.workbenchReady
          && result.happyPathReady
          && (renderer !== "react" || Boolean(
            result.parityGatePassed
            && result.happyPathSystemReady
            && result.happyPathExperimentsReady
            && result.happyPathPaperOpsReady
            && result.happyPathAssistantReady
            && result.happyPathLaunchReady
          ))
          && result.shellReady
          && result.rendererMode === renderer
        );

    if (!passed) {
      if (stdout.trim()) console.error(stdout.trim());
      if (stderr.trim()) console.error(stderr.trim());
      throw new Error(`Desktop smoke (${mode}) failed: ${JSON.stringify(result)}`);
    }

    let persistedWorkspace = null;
    for (let attempt = 0; attempt < 50; attempt += 1) {
      try {
        const persistedWorkspaceRaw = await fs.readFile(workspaceStatePath, "utf8");
        if (!persistedWorkspaceRaw.trim()) {
          throw new SyntaxError("Desktop workspace_state.json is still empty.");
        }
        persistedWorkspace = JSON.parse(persistedWorkspaceRaw);
        break;
      } catch (error) {
        const incompleteJson = error instanceof SyntaxError;
        if (error?.code !== "ENOENT" && !incompleteJson) throw error;
        await new Promise((resolve) => setTimeout(resolve, 120));
      }
    }
    if (!persistedWorkspace) {
      console.warn("Desktop smoke warning: workspace_state.json was not readable after Electron exit.");
    } else {
      const restoredPaperTab = Array.isArray(persistedWorkspace.tabs)
        && persistedWorkspace.tabs.some((tab) => tab && tab.id === "paper-ops" && tab.kind === "paper");
      if (!restoredPaperTab) {
        throw new Error(`Desktop smoke persistence failed: ${JSON.stringify(persistedWorkspace)}`);
      }
    }

    console.log(
      mode === "real-path"
        ? `Desktop smoke real-path passed via ${result.serverUrl}`
        : (result.serverReady
            ? `Desktop smoke fallback passed via ${result.serverUrl}`
            : "Desktop smoke fallback passed via local runs fallback"),
    );
    if (renderer === "react") {
      console.log(
        `React parity gate (${result.parityGateName || "react-parity-v1"}): `
        + `runs=${Boolean(result.happyPathRunsReady)} `
        + `runDetail=${Boolean(result.happyPathRunDetailReady)} `
        + `artifacts=${Boolean(result.happyPathArtifactsReady)} `
        + `candidates=${Boolean(result.happyPathCandidatesReady)} `
        + `compare=${Boolean(result.happyPathCompareReady)} `
        + `system=${Boolean(result.happyPathSystemReady)} `
        + `experiments=${Boolean(result.happyPathExperimentsReady)} `
        + `paperOps=${Boolean(result.happyPathPaperOpsReady)} `
        + `assistant=${Boolean(result.happyPathAssistantReady)} `
        + `launch=${Boolean(result.happyPathLaunchReady)} `
        + `passed=${Boolean(result.parityGatePassed)}`,
      );
    }
  } finally {
    if (seededRunsIndex) {
      await fs.rm(smokeRunsIndexPath, { force: true }).catch(() => {});
    }
  }
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
