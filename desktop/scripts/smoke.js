const fs = require("fs/promises");
const os = require("os");
const path = require("path");
const { spawn } = require("child_process");

async function main() {
  const desktopRoot = path.resolve(__dirname, "..");
  const projectRoot = path.resolve(desktopRoot, "..");
  const electronBinary = require("electron");
  const electronArgs = process.platform === "linux" ? ["--no-sandbox", "."] : ["."];
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
    const child = spawn(electronBinary, electronArgs, {
      cwd: desktopRoot,
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"],
      env: {
        ...process.env,
        QUANTLAB_DESKTOP_SMOKE: "1",
        QUANTLAB_DESKTOP_SMOKE_OUTPUT: outputPath,
        QUANTLAB_DESKTOP_OUTPUTS_ROOT: desktopOutputsRoot,
        QUANTLAB_DESKTOP_DISABLE_SERVER_BOOT: "1",
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
    let result = null;
    for (let attempt = 0; attempt < 10; attempt += 1) {
      try {
        const raw = await fs.readFile(outputPath, "utf8");
        result = JSON.parse(raw);
        break;
      } catch (error) {
        if (error?.code !== "ENOENT") throw error;
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

    if (exitCode !== 0 || !result.bridgeReady || !result.shellReady) {
      if (stdout.trim()) console.error(stdout.trim());
      if (stderr.trim()) console.error(stderr.trim());
      throw new Error(`Desktop smoke failed: ${JSON.stringify(result)}`);
    }

    const persistedWorkspaceRaw = await fs.readFile(workspaceStatePath, "utf8");
    const persistedWorkspace = JSON.parse(persistedWorkspaceRaw);
    const restoredPaperTab = Array.isArray(persistedWorkspace.tabs)
      && persistedWorkspace.tabs.some((tab) => tab && tab.id === "paper-ops" && tab.kind === "paper");
    if (!restoredPaperTab || persistedWorkspace.active_tab_id !== "paper-ops") {
      throw new Error(`Desktop smoke persistence failed: ${JSON.stringify(persistedWorkspace)}`);
    }

    console.log(
      result.serverReady
        ? `Desktop smoke passed via ${result.serverUrl}`
        : "Desktop smoke passed via local runs fallback",
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
