const fs = require("fs/promises");
const os = require("os");
const path = require("path");
const { spawn } = require("child_process");

function parseSmokeMode(argv = process.argv.slice(2)) {
  const explicitMode = argv
    .map((value) => String(value || "").trim())
    .find((value) => value.startsWith("--mode="));
  const mode = explicitMode ? explicitMode.split("=", 2)[1] : "fallback";
  return mode === "real-path" ? "real-path" : "fallback";
}

async function main() {
  const mode = parseSmokeMode();
  const requireRealPath = mode === "real-path";
  const desktopRoot = path.resolve(__dirname, "..");
  const checkoutRoot = path.resolve(desktopRoot, "..");
  const workspaceRoot = path.resolve(checkoutRoot, "..");
  const canonicalProjectRoot = path.join(workspaceRoot, "quant_lab");
  const projectRoot = await fs.access(path.join(canonicalProjectRoot, "research_ui", "server.py"))
    .then(() => canonicalProjectRoot)
    .catch(() => checkoutRoot);
  const electronBinary = require("electron");
  const tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "quantlab-desktop-smoke-"));
  const outputPath = path.join(tempRoot, "result.json");
  const desktopOutputsRoot = path.join(tempRoot, "outputs");
  const workspaceStatePath = path.join(desktopOutputsRoot, "desktop", "workspace_state.json");
  const projectRunsDir = path.join(projectRoot, "outputs", "runs");
  const projectRunsIndexPath = path.join(projectRunsDir, "runs_index.json");
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
    await fs.access(projectRunsIndexPath);
  } catch (_error) {
    await fs.mkdir(projectRunsDir, { recursive: true });
    await fs.writeFile(
      projectRunsIndexPath,
      `${JSON.stringify({
        updated_at: new Date().toISOString(),
        runs: [
          {
            run_id: "smoke_run_001",
            mode: "grid",
            ticker: "ETH-USD",
            created_at: new Date().toISOString(),
            git_commit: "smoke000",
            total_return: 0.12,
            sharpe_simple: 1.1,
            max_drawdown: -0.08,
            trades: 4,
            path: path.join(projectRoot, "outputs", "runs", "smoke_run_001"),
          },
        ],
      }, null, 2)}\n`,
      "utf8",
    );
    seededRunsIndex = true;
  }

  try {
    const child = spawn(electronBinary, ["."], {
      cwd: desktopRoot,
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"],
      env: {
        ...process.env,
        QUANTLAB_DESKTOP_SMOKE: "1",
        QUANTLAB_DESKTOP_SMOKE_MODE: mode,
        QUANTLAB_DESKTOP_SMOKE_REQUIRE_SERVER: requireRealPath ? "1" : "0",
        QUANTLAB_DESKTOP_SMOKE_OUTPUT: outputPath,
        QUANTLAB_DESKTOP_OUTPUTS_ROOT: desktopOutputsRoot,
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

    const raw = await fs.readFile(outputPath, "utf8");
    const result = JSON.parse(raw);

    const smokeFailed = exitCode !== 0
      || !result.bridgeReady
      || !result.shellReady
      || (requireRealPath && (!result.serverReady || !result.apiReady));

    if (smokeFailed) {
      if (stdout.trim()) console.error(stdout.trim());
      if (stderr.trim()) console.error(stderr.trim());
      throw new Error(`Desktop ${mode} smoke failed: ${JSON.stringify(result)}`);
    }

    const persistedWorkspaceRaw = await fs.readFile(workspaceStatePath, "utf8");
    const persistedWorkspace = JSON.parse(persistedWorkspaceRaw);
    const restoredPaperTab = Array.isArray(persistedWorkspace.tabs)
      && persistedWorkspace.tabs.some((tab) => tab && tab.id === "paper-ops" && tab.kind === "paper");
    if (!restoredPaperTab || persistedWorkspace.active_tab_id !== "paper-ops") {
      throw new Error(`Desktop smoke persistence failed: ${JSON.stringify(persistedWorkspace)}`);
    }

    console.log(
      requireRealPath
        ? `Desktop real-path smoke passed via ${result.serverUrl}`
        : result.serverReady
          ? `Desktop fallback smoke passed via ${result.serverUrl}`
          : "Desktop fallback smoke passed via local runs fallback",
    );
  } finally {
    if (seededRunsIndex) {
      await fs.rm(projectRunsIndexPath, { force: true }).catch(() => {});
    }
  }
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
