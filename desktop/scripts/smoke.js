const fs = require("fs/promises");
const os = require("os");
const path = require("path");
const { spawn } = require("child_process");

async function main() {
  const desktopRoot = path.resolve(__dirname, "..");
  const electronBinary = require("electron");
  const outputDir = await fs.mkdtemp(path.join(os.tmpdir(), "quantlab-desktop-smoke-"));
  const outputPath = path.join(outputDir, "result.json");

  const child = spawn(electronBinary, ["."], {
    cwd: desktopRoot,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
    env: {
      ...process.env,
      QUANTLAB_DESKTOP_SMOKE: "1",
      QUANTLAB_DESKTOP_SMOKE_OUTPUT: outputPath,
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
  }, 30000);

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

  console.log(`Desktop smoke passed via ${result.serverUrl}`);
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
