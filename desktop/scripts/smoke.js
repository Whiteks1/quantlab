const fs = require("fs/promises");
const os = require("os");
const path = require("path");
const { spawn } = require("child_process");

async function main() {
  const desktopRoot = path.resolve(__dirname, "..");
  const electronBinary = require("electron");
  const tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "quantlab-desktop-smoke-"));
  const outputPath = path.join(tempRoot, "result.json");
  const desktopOutputsRoot = path.join(tempRoot, "outputs");
  const workspaceStatePath = path.join(desktopOutputsRoot, "desktop", "workspace_state.json");

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

  const child = spawn(electronBinary, ["."], {
    cwd: desktopRoot,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
    env: {
      ...process.env,
      QUANTLAB_DESKTOP_SMOKE: "1",
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

  if (exitCode !== 0 || !result.bridgeReady || !result.serverReady || !result.apiReady) {
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

  console.log(`Desktop smoke passed via ${result.serverUrl}`);
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
