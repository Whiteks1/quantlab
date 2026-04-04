import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DESKTOP_ROOT = __dirname;
const PROJECT_ROOT = path.resolve(DESKTOP_ROOT, "..");
const PYTHON_EXECUTABLE = process.env.QUANTLAB_PYTHON || "python";
const MAX_OUTPUT_CHARS = 12000;

function truncateText(text) {
  if (text.length <= MAX_OUTPUT_CHARS) return text;
  return `${text.slice(0, MAX_OUTPUT_CHARS)}\n...[truncated]`;
}

function runProcess(command, args, options = {}) {
  return new Promise((resolve) => {
    const child = spawn(command, args, {
      cwd: options.cwd || PROJECT_ROOT,
      env: { ...process.env, ...(options.env || {}) },
      windowsHide: true,
      shell: false,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += String(chunk || "");
    });
    child.stderr.on("data", (chunk) => {
      stderr += String(chunk || "");
    });

    const timeoutMs = options.timeoutMs || 120000;
    const timer = setTimeout(() => {
      child.kill();
      resolve({
        exitCode: 124,
        stdout,
        stderr: `${stderr}\nCommand timed out after ${timeoutMs}ms`.trim(),
      });
    }, timeoutMs);

    child.on("error", (error) => {
      clearTimeout(timer);
      resolve({
        exitCode: 1,
        stdout,
        stderr: error.message || String(error),
      });
    });

    child.on("exit", (code) => {
      clearTimeout(timer);
      resolve({
        exitCode: code ?? 1,
        stdout,
        stderr,
      });
    });
  });
}

async function runPythonCli(args, timeoutMs = 120000) {
  return runProcess(PYTHON_EXECUTABLE, ["main.py", ...args], {
    cwd: PROJECT_ROOT,
    timeoutMs,
  });
}

async function formatProcessResult(label, result, commandLine) {
  const sections = [
    `Command: ${commandLine}`,
    `Exit code: ${result.exitCode}`,
  ];
  if (result.stdout.trim()) {
    sections.push(`stdout:\n${truncateText(result.stdout.trim())}`);
  }
  if (result.stderr.trim()) {
    sections.push(`stderr:\n${truncateText(result.stderr.trim())}`);
  }
  return {
    content: [
      {
        type: "text",
        text: `[${label}]\n${sections.join("\n\n")}\n`,
      },
    ],
  };
}

async function main() {
  const server = new McpServer({
    name: "quantlab-local",
    version: "0.1.0",
  });

  server.registerTool("quantlab_check", {
    description: "Run the standard QuantLab health check.",
  }, async () => {
    const result = await runPythonCli(["--check"], 120000);
    return formatProcessResult("quantlab_check", result, "python main.py --check");
  });

  server.registerTool("quantlab_version", {
    description: "Return the QuantLab CLI version.",
  }, async () => {
    const result = await runPythonCli(["--version"], 30000);
    return formatProcessResult("quantlab_version", result, "python main.py --version");
  });

  server.registerTool("quantlab_runs_list", {
    description: "List indexed QuantLab runs.",
  }, async () => {
    const result = await runPythonCli(["--runs-list"], 120000);
    return formatProcessResult("quantlab_runs_list", result, "python main.py --runs-list");
  });

  server.registerTool("quantlab_paper_sessions_health", {
    description: "Summarize the health of QuantLab paper sessions.",
  }, async () => {
    const result = await runPythonCli(["--paper-sessions-health"], 120000);
    return formatProcessResult(
      "quantlab_paper_sessions_health",
      result,
      "python main.py --paper-sessions-health",
    );
  });

  server.registerTool("quantlab_desktop_smoke", {
    description: "Run the QuantLab desktop smoke test.",
  }, async () => {
    const result = await runProcess("node", ["scripts/smoke.js"], {
      cwd: DESKTOP_ROOT,
      timeoutMs: 180000,
    });
    return formatProcessResult("quantlab_desktop_smoke", result, "node scripts/smoke.js");
  });

  server.registerTool("quantlab_read_file", {
    description: "Read a text file within the QuantLab repository.",
    inputSchema: {
      relative_path: z.string().describe("Path relative to the QuantLab repository root"),
    },
  }, async ({ relative_path }) => {
    const resolvedPath = path.resolve(PROJECT_ROOT, relative_path);
    const relative = path.relative(PROJECT_ROOT, resolvedPath);
    if (relative.startsWith("..") || path.isAbsolute(relative)) {
      return {
        content: [
          {
            type: "text",
            text: `Refusing to read outside the QuantLab repository: ${relative_path}`,
          },
        ],
        isError: true,
      };
    }

    try {
      const data = await fs.readFile(resolvedPath, "utf8");
      return {
        content: [
          {
            type: "text",
            text: truncateText(data),
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Failed to read ${relative_path}: ${error.message || String(error)}`,
          },
        ],
        isError: true,
      };
    }
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
