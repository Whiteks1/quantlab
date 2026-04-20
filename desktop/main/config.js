// @ts-check

const path = require("path");

const DESKTOP_ROOT = path.resolve(__dirname, "..");
const PROJECT_ROOT = path.resolve(DESKTOP_ROOT, "..");
const WORKSPACE_ROOT = path.resolve(PROJECT_ROOT, "..");
const SERVER_SCRIPT = path.join(PROJECT_ROOT, "research_ui", "server.py");
const OUTPUTS_ROOT = process.env.QUANTLAB_DESKTOP_OUTPUTS_ROOT
  ? path.resolve(process.env.QUANTLAB_DESKTOP_OUTPUTS_ROOT)
  : path.join(PROJECT_ROOT, "outputs");
const ALLOWED_LOCAL_ROOTS = [PROJECT_ROOT, OUTPUTS_ROOT];
const DESKTOP_OUTPUTS_ROOT = path.join(OUTPUTS_ROOT, "desktop");
const CANDIDATES_STORE_PATH = path.join(DESKTOP_OUTPUTS_ROOT, "candidates_shortlist.json");
const SWEEP_DECISION_STORE_PATH = path.join(DESKTOP_OUTPUTS_ROOT, "sweep_decision_handoff.json");
const WORKSPACE_STORE_PATH = path.join(DESKTOP_OUTPUTS_ROOT, "workspace_state.json");
const STEPBIT_APP_ROOT = path.join(WORKSPACE_ROOT, "stepbit-app");
const STEPBIT_APP_CONFIG_PATH = path.join(STEPBIT_APP_ROOT, "config.yaml");
const MAX_DIRECTORY_ENTRIES = 240;
const RESEARCH_UI_URLS = [
  "http://127.0.0.1:8000",
  "http://localhost:8000",
];
const RESEARCH_UI_HEALTH_PATH = "/api/paper-sessions-health";
const RESEARCH_UI_STARTUP_TIMEOUT_MS = 25000;
const ELECTRON_STATE_ROOT = path.join(DESKTOP_OUTPUTS_ROOT, "electron");
const IS_SMOKE_RUN = process.env.QUANTLAB_DESKTOP_SMOKE === "1";
const SMOKE_MODE = process.env.QUANTLAB_DESKTOP_SMOKE_MODE === "real-path" ? "real-path" : "fallback";
const SMOKE_OUTPUT_PATH = process.env.QUANTLAB_DESKTOP_SMOKE_OUTPUT || "";
const SKIP_RESEARCH_UI_BOOT = process.env.QUANTLAB_DESKTOP_DISABLE_SERVER_BOOT === "1";

module.exports = {
  DESKTOP_ROOT,
  PROJECT_ROOT,
  WORKSPACE_ROOT,
  SERVER_SCRIPT,
  OUTPUTS_ROOT,
  ALLOWED_LOCAL_ROOTS,
  DESKTOP_OUTPUTS_ROOT,
  CANDIDATES_STORE_PATH,
  SWEEP_DECISION_STORE_PATH,
  WORKSPACE_STORE_PATH,
  STEPBIT_APP_ROOT,
  STEPBIT_APP_CONFIG_PATH,
  MAX_DIRECTORY_ENTRIES,
  RESEARCH_UI_URLS,
  RESEARCH_UI_HEALTH_PATH,
  RESEARCH_UI_STARTUP_TIMEOUT_MS,
  ELECTRON_STATE_ROOT,
  IS_SMOKE_RUN,
  SMOKE_MODE,
  SMOKE_OUTPUT_PATH,
  SKIP_RESEARCH_UI_BOOT,
};
