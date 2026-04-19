import http.server
import json
import socketserver
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.parse import unquote
from urllib.request import Request, urlopen
from uuid import uuid4

PORT = 8000
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESEARCH_UI_STATIC_ROOT = PROJECT_ROOT / "research_ui"
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

LAUNCH_HISTORY_LIMIT = 12
LAUNCH_JOBS: list[dict[str, object]] = []
LAUNCH_LOCK = Lock()
STEPBIT_START_LOCK = Lock()
STEPBIT_START_STATE: dict[str, object] = {
    "status": "idle",
    "requested_at": 0.0,
    "actions": [],
}
STEPBIT_FRONTEND_URLS = [
    "http://127.0.0.1:5173/",
    "http://localhost:5173/",
]
STEPBIT_BACKEND_URLS = [
    "http://127.0.0.1:8080/",
    "http://localhost:8080/",
]
STEPBIT_CORE_URLS = [
    "http://127.0.0.1:3000/",
    "http://localhost:3000/",
]

from quantlab.cli.broker_order_validations import (
    build_broker_submission_alerts,
    build_broker_submission_health,
)
from quantlab.cli.hyperliquid_submit_sessions import (
    build_hyperliquid_submission_alerts,
    build_hyperliquid_submission_health,
)
from quantlab.cli.paper_sessions import (
    DEFAULT_PAPER_STALE_MINUTES,
    build_paper_sessions_alerts,
    build_paper_sessions_health,
)
from quantlab.pretrade.handoff import (
    PRETRADE_HANDOFF_VALIDATION_CONTRACT_TYPE,
    PRETRADE_HANDOFF_VALIDATION_FILENAME,
)

STEPBIT_APP_SURFACE_SPECS = [
    {
        "id": "dashboard",
        "label": "Dashboard",
        "category": "Operations",
        "route": "/",
        "file": "web/src/pages/Dashboard.tsx",
        "summary": "Health, readiness, models, requests, token load, and runtime visibility.",
    },
    {
        "id": "system",
        "label": "System",
        "category": "Operations",
        "route": "/system",
        "file": "web/src/pages/System.tsx",
        "summary": "Readiness-oriented runtime surface for API, database, and core diagnostics.",
    },
    {
        "id": "chat",
        "label": "Chat",
        "category": "Workspace",
        "route": "/chat",
        "file": "web/src/pages/Chat.tsx",
        "summary": "Streaming chat with provider/model selection and persistent local sessions.",
    },
    {
        "id": "database",
        "label": "Database",
        "category": "Data",
        "route": "/database",
        "file": "web/src/pages/Database.tsx",
        "summary": "DuckDB-backed local memory and data inspection surface.",
    },
    {
        "id": "sql_explorer",
        "label": "SQL Explorer",
        "category": "Data",
        "route": "/db-explorer",
        "file": "web/src/pages/DatabaseExplorer.tsx",
        "summary": "Ad-hoc SQL workspace for querying the Stepbit local database.",
    },
    {
        "id": "skills",
        "label": "Skills",
        "category": "Workspace",
        "route": "/skills",
        "file": "web/src/pages/Skills.tsx",
        "summary": "Reusable prompt assets and imported personas for operator workflows.",
    },
    {
        "id": "mcp_tools",
        "label": "MCP Tools",
        "category": "Tooling",
        "route": "/mcp-tools",
        "file": "web/src/pages/McpTools.tsx",
        "summary": "Tool discovery and execution playground for registered MCP providers.",
    },
    {
        "id": "reasoning",
        "label": "Reasoning",
        "category": "Automation",
        "route": "/reasoning",
        "file": "web/src/pages/ReasoningPlayground.tsx",
        "summary": "Graph-based reasoning playground for ad-hoc DAG execution.",
    },
    {
        "id": "pipelines",
        "label": "Pipelines",
        "category": "Automation",
        "route": "/pipelines",
        "file": "web/src/pages/Pipelines.tsx",
        "summary": "CRUD and execution flow for deterministic cognitive pipelines.",
    },
    {
        "id": "goals",
        "label": "Goals",
        "category": "Automation",
        "route": "/goals",
        "file": "web/src/pages/Goals.tsx",
        "summary": "Planner-first entry point that turns natural-language goals into runs.",
    },
    {
        "id": "scheduled_jobs",
        "label": "Scheduled Jobs",
        "category": "Automation",
        "route": "/scheduled-jobs",
        "file": "web/src/pages/ScheduledJobs.tsx",
        "summary": "Cron-backed recurring automation proxied into stepbit-core.",
    },
    {
        "id": "triggers",
        "label": "Triggers",
        "category": "Automation",
        "route": "/triggers",
        "file": "web/src/pages/Triggers.tsx",
        "summary": "Reactive event rules that publish work into the core runtime.",
    },
    {
        "id": "executions",
        "label": "Executions",
        "category": "Operations",
        "route": "/executions",
        "file": "web/src/pages/ExecutionHistory.tsx",
        "summary": "Execution history for pipelines, goals, and operator-initiated actions.",
    },
    {
        "id": "settings",
        "label": "Settings",
        "category": "Workspace",
        "route": "/settings",
        "file": "web/src/pages/Settings.tsx",
        "summary": "Local application configuration and provider controls.",
    },
]

STEPBIT_CORE_CAPABILITY_SPECS = [
    {
        "id": "orchestrator",
        "label": "Unified Orchestrator",
        "category": "Runtime",
        "path": "src/orchestrator",
        "summary": "Coordinates planning, graphs, pipelines, resources, and event streaming.",
    },
    {
        "id": "planner",
        "label": "Planner Core",
        "category": "Reasoning",
        "path": "src/planner",
        "summary": "Goal decomposition, plan validation, and graph translation.",
    },
    {
        "id": "reasoning",
        "label": "Reasoning Engine",
        "category": "Reasoning",
        "path": "src/reasoning",
        "summary": "DAG execution with traceable node lifecycle and streaming feedback.",
    },
    {
        "id": "pipelines",
        "label": "Pipeline Runtime",
        "category": "Automation",
        "path": "src/pipelines",
        "summary": "Structured multi-stage workflows with shared context and streaming output.",
    },
    {
        "id": "mcp",
        "label": "MCP Framework",
        "category": "Tooling",
        "path": "src/mcp",
        "summary": "Native and external MCP providers with tool discovery and invocation.",
    },
    {
        "id": "cron",
        "label": "Cron Scheduler",
        "category": "Automation",
        "path": "src/cron",
        "summary": "Recurring jobs, persistence, retries, and manual triggers.",
    },
    {
        "id": "events",
        "label": "Event Bus & Triggers",
        "category": "Automation",
        "path": "src/events",
        "summary": "Reactive automation through event publishing and trigger matching.",
    },
    {
        "id": "inference",
        "label": "Inference Backends",
        "category": "Runtime",
        "path": "src/inference",
        "summary": "Backend-aware local inference, model loading, and session execution.",
    },
    {
        "id": "scheduler",
        "label": "Token Scheduler",
        "category": "Runtime",
        "path": "src/scheduler",
        "summary": "Budget-aware scheduling and batching for active sessions.",
    },
    {
        "id": "health",
        "label": "Health & Metrics",
        "category": "Operations",
        "path": "src/health",
        "summary": "Liveness, readiness, and Prometheus-style observability surfaces.",
    },
    {
        "id": "distributed",
        "label": "Distributed Hooks",
        "category": "Operations",
        "path": "src/distributed",
        "summary": "Controller/worker execution path for remote delegation and scaling.",
    },
]

STEPBIT_COMPATIBILITY_SURFACES = [
    {
        "id": "models",
        "label": "Model Catalog",
        "method": "GET",
        "path": "/v1/models",
        "category": "Inference",
        "summary": "List locally discovered models and backend-aware runtime specs.",
    },
    {
        "id": "chat",
        "label": "Chat Completions",
        "method": "POST",
        "path": "/v1/chat/completions",
        "category": "Inference",
        "summary": "OpenAI-style chat interface with optional SSE streaming.",
    },
    {
        "id": "goals",
        "label": "Goal Runs",
        "method": "POST",
        "path": "/v1/goals/execute",
        "category": "Reasoning",
        "summary": "High-level goal execution entry point owned by the planner/runtime.",
    },
    {
        "id": "reasoning",
        "label": "Reasoning Graphs",
        "method": "POST",
        "path": "/v1/reasoning/execute",
        "category": "Reasoning",
        "summary": "Direct execution of reasoning DAGs with streamed progress variants.",
    },
    {
        "id": "pipelines",
        "label": "Pipelines",
        "method": "POST",
        "path": "/v1/pipelines/execute",
        "category": "Automation",
        "summary": "Deterministic pipeline execution for structured workflows.",
    },
    {
        "id": "mcp_tools",
        "label": "MCP Tools",
        "method": "GET",
        "path": "/v1/mcp/tools",
        "category": "Tooling",
        "summary": "Discover registered tools and their schemas before invocation.",
    },
    {
        "id": "cron",
        "label": "Cron Jobs",
        "method": "GET",
        "path": "/v1/cron/jobs",
        "category": "Automation",
        "summary": "Inspect recurring jobs and operational scheduling state.",
    },
    {
        "id": "events",
        "label": "Events & Triggers",
        "method": "GET",
        "path": "/v1/triggers",
        "category": "Automation",
        "summary": "List trigger registrations used for reactive workflows.",
    },
    {
        "id": "metrics",
        "label": "Metrics",
        "method": "GET",
        "path": "/metrics",
        "category": "Operations",
        "summary": "Prometheus-style runtime metrics for requests, tokens, and sessions.",
    },
    {
        "id": "health",
        "label": "Health",
        "method": "GET",
        "path": "/ready",
        "category": "Operations",
        "summary": "Readiness probe that reports if the runtime is loaded and usable.",
    },
]

META_TRADE_PRODUCT_SURFACE_SPECS = [
    {
        "id": "risk_calculator",
        "label": "Risk Calculator",
        "category": "Workspace",
        "path": "index.html",
        "summary": "Browser workbench for capital, risk, entry, stop, target, fees, and slippage.",
    },
    {
        "id": "scenario_comparison",
        "label": "Scenario Comparison",
        "category": "Workspace",
        "path": "web/risk-ui.js",
        "summary": "Saved scenarios table with comparison workflow and persistence.",
    },
    {
        "id": "history",
        "label": "Trade History",
        "category": "Workspace",
        "path": "web/risk-ui.js",
        "summary": "Searchable history with strategy, notes, filters, and timestamps.",
    },
    {
        "id": "trade_plan_exports",
        "label": "Trade Plan Exports",
        "category": "Exports",
        "path": "web/shared.js",
        "summary": "JSON and CSV exports for deterministic trade-plan serialization.",
    },
    {
        "id": "quantlab_handoff",
        "label": "QuantLab Handoff Export",
        "category": "Exports",
        "path": "cli/trade-plan.js",
        "summary": "Bounded handoff generation for downstream QuantLab intake.",
    },
    {
        "id": "mini_backtester",
        "label": "Mini Backtester",
        "category": "Analysis",
        "path": "web/backtest-ui.js",
        "summary": "Visual moving-average backtester with signals, trades, and equity curve.",
    },
]

META_TRADE_ENGINE_MODULE_SPECS = [
    {
        "id": "risk_core_js",
        "label": "Shared JS Risk Core",
        "category": "Core",
        "path": "risk-core.js",
        "summary": "Canonical trade-plan generation and deterministic serialization in JavaScript.",
    },
    {
        "id": "browser_shared",
        "label": "Browser Shared Utilities",
        "category": "Browser",
        "path": "web/shared.js",
        "summary": "Formatting, form reading, persistence, CSV helpers, and file downloads.",
    },
    {
        "id": "browser_risk_ui",
        "label": "Risk UI Module",
        "category": "Browser",
        "path": "web/risk-ui.js",
        "summary": "Main calculator, scenarios, history, and export interactions.",
    },
    {
        "id": "browser_backtester",
        "label": "Backtester Module",
        "category": "Browser",
        "path": "web/backtest-ui.js",
        "summary": "Client-side analytical backtester and chart rendering surface.",
    },
    {
        "id": "browser_bootstrap",
        "label": "Browser Bootstrap",
        "category": "Browser",
        "path": "web/main.js",
        "summary": "Final web bootstrap that wires the bounded browser app together.",
    },
    {
        "id": "headless_cli",
        "label": "Headless CLI",
        "category": "CLI",
        "path": "cli/trade-plan.js",
        "summary": "DOM-free deterministic CLI path for plans and QuantLab handoffs.",
    },
    {
        "id": "cpp_engine",
        "label": "C++ Engine",
        "category": "Parity",
        "path": "cpp/risk_engine.cpp",
        "summary": "Alternate runtime for parity, cross-validation, and deterministic calculations.",
    },
    {
        "id": "cpp_trade_runner",
        "label": "C++ Trade Plan Runner",
        "category": "Parity",
        "path": "cpp/trade_plan_runner.cpp",
        "summary": "Cross-runtime runner for canonical trade-plan parity checks.",
    },
]

META_TRADE_VALIDATION_SURFACES = [
    {
        "id": "js_tests",
        "label": "JS Core Tests",
        "category": "Tests",
        "path": "tests/run_js_tests.js",
        "summary": "Baseline verification for JavaScript risk and trade-plan flows.",
    },
    {
        "id": "cli_tests",
        "label": "CLI Tests",
        "category": "Tests",
        "path": "tests/run_cli_tests.js",
        "summary": "Headless CLI verification without depending on the browser surface.",
    },
    {
        "id": "contract_fixture_tests",
        "label": "Contract Fixture Tests",
        "category": "Tests",
        "path": "tests/run_contract_fixture_tests.js",
        "summary": "Checks deterministic handoff artifacts against canonical fixtures.",
    },
    {
        "id": "cross_runtime_tests",
        "label": "JS/C++ Parity Tests",
        "category": "Parity",
        "path": "tests/run_cross_tests.js",
        "summary": "Cross-runtime parity checks for calculation metrics between JS and C++.",
    },
    {
        "id": "trade_plan_parity",
        "label": "Trade Plan Parity",
        "category": "Parity",
        "path": "tests/run_trade_plan_cross_tests.js",
        "summary": "Trade-plan parity checks between JavaScript and C++ runners.",
    },
    {
        "id": "ui_smoke",
        "label": "UI Smoke Tests",
        "category": "Tests",
        "path": "tests/ui/risk-calculator.spec.js",
        "summary": "Browser smoke coverage for the main workbench interaction path.",
    },
    {
        "id": "ci_contract_parity",
        "label": "Contract & Parity CI",
        "category": "CI",
        "path": ".github/workflows/contract-parity-ci.yml",
        "summary": "CI workflow enforcing contract stability and cross-runtime parity.",
    },
]

META_TRADE_CONTRACT_ARTIFACTS = [
    {
        "id": "workbench_roadmap",
        "label": "Workbench Roadmap",
        "category": "Docs",
        "path": "docs/pretrade-workbench-roadmap.md",
        "summary": "Repository purpose, boundary, and critical path for upstream planning.",
    },
    {
        "id": "quantlab_handoff_contract",
        "label": "QuantLab Handoff Contract",
        "category": "Docs",
        "path": "docs/quantlab-handoff-contract.md",
        "summary": "Bounded contract for the downstream QuantLab handoff JSON.",
    },
    {
        "id": "handoff_example",
        "label": "Handoff Example Request",
        "category": "Examples",
        "path": "examples/quantlab_handoff_request.json",
        "summary": "Example request used for deterministic headless handoff generation.",
    },
    {
        "id": "handoff_fixture",
        "label": "Expected QuantLab Handoff",
        "category": "Fixtures",
        "path": "tests/fixtures/expected_quantlab_handoff.json",
        "summary": "Canonical fixture for validating the emitted QuantLab handoff artifact.",
    },
]


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        request_path = unquote(self.path.split("?", 1)[0].split("#", 1)[0])
        meta_trade_repo = _resolve_meta_trade_repo(PROJECT_ROOT)
        if request_path == '/external/meta-trade' or request_path.startswith('/external/meta-trade/'):
            return self._serve_external_static(meta_trade_repo, '/external/meta-trade/', request_path)
        if request_path.startswith('/api/paper-sessions-health'):
            payload, status = build_paper_health_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if request_path.startswith('/api/paper-sessions-alerts'):
            payload, status = build_paper_alerts_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if request_path.startswith('/api/broker-submissions-health'):
            payload, status = build_broker_health_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if request_path.startswith('/api/hyperliquid-surface'):
            payload, status = build_hyperliquid_surface_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if request_path.startswith('/api/pretrade-handoff-intake'):
            payload, status = build_pretrade_handoff_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if request_path.startswith('/api/stepbit-workspace'):
            payload, status = build_stepbit_workspace_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if request_path.startswith('/api/meta-trade-workspace'):
            payload, status = build_meta_trade_workspace_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)
        if request_path.startswith('/api/launch-control'):
            payload, status = build_launch_control_payload(PROJECT_ROOT)
            return self._send_json(payload, status=status)

        # Redirect root to research_ui/index.html to ensure relative asset paths work
        if request_path == '/' or request_path == '':
            self.send_response(302)
            self.send_header('Location', '/research_ui/index.html')
            self.end_headers()
            return
        if request_path == '/research_ui':
            self.send_response(302)
            self.send_header('Location', '/research_ui/index.html')
            self.end_headers()
            return
        if request_path.startswith('/research_ui/'):
            return self._serve_research_ui_static(request_path)
        self.send_error(404, "Not found")

    def do_POST(self):
        request_path = unquote(self.path.split("?", 1)[0].split("#", 1)[0])
        if request_path.startswith('/api/stepbit-workspace/start'):
            try:
                body = self._read_json_body()
                payload, status = start_stepbit_workspace(PROJECT_ROOT, body)
                return self._send_json(payload, status=status)
            except ValueError as exc:
                return self._send_json({"status": "error", "message": str(exc)}, status=400)
            except Exception as exc:  # noqa: BLE001
                return self._send_json({"status": "error", "message": str(exc)}, status=500)
        if request_path.startswith('/api/launch-control'):
            try:
                body = self._read_json_body()
                job_payload, status = launch_quantlab_job(PROJECT_ROOT, body)
                return self._send_json(job_payload, status=status)
            except ValueError as exc:
                return self._send_json({"status": "error", "message": str(exc)}, status=400)
            except Exception as exc:  # noqa: BLE001
                return self._send_json({"status": "error", "message": str(exc)}, status=500)
        self.send_error(404, "Not found")

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON body: {exc.msg}") from exc

    def _serve_external_static(self, repo_root: Path, prefix: str, request_path: str):
        relative_path = request_path[len(prefix):].lstrip("/")
        repo_root_resolved = repo_root.resolve()
        target = (repo_root_resolved / relative_path) if relative_path else (repo_root_resolved / "index.html")

        try:
            target = target.resolve()
            target.relative_to(repo_root_resolved)
        except Exception:  # noqa: BLE001
            self.send_error(403, "Forbidden")
            return

        if target.is_dir():
            target = target / "index.html"

        if not target.exists() or not target.is_file():
            self.send_error(404, "File not found")
            return

        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(str(target)))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_research_ui_static(self, request_path: str):
        relative_path = request_path[len('/research_ui/'):].lstrip('/')
        root_resolved = RESEARCH_UI_STATIC_ROOT.resolve()
        target = (root_resolved / relative_path) if relative_path else (root_resolved / "index.html")

        try:
            target = target.resolve()
            relative_parts = target.relative_to(root_resolved).parts
        except Exception:  # noqa: BLE001
            self.send_error(403, "Forbidden")
            return

        if any(part.startswith('.') for part in relative_parts):
            self.send_error(403, "Forbidden")
            return

        if target.is_dir():
            target = target / "index.html"

        if not target.exists() or not target.is_file():
            self.send_error(404, "File not found")
            return

        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(str(target)))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def build_paper_health_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    paper_root = root / "outputs" / "paper_sessions"

    if not paper_root.exists():
        return {
            "status": "ok",
            "available": False,
            "root_dir": str(paper_root),
            "message": "No paper session root found yet.",
            "total_sessions": 0,
            "status_counts": {},
            "latest_session_id": None,
            "latest_session_status": None,
            "latest_session_at": None,
            "latest_issue_session_id": None,
            "latest_issue_status": None,
            "latest_issue_at": None,
            "latest_issue_error_type": None,
        }, 200

    try:
        payload = build_paper_sessions_health(paper_root)
        payload["status"] = "ok"
        payload["available"] = True
        return payload, 200
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "available": False,
            "root_dir": str(paper_root),
            "message": str(exc),
        }, 500


def build_paper_alerts_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    paper_root = root / "outputs" / "paper_sessions"

    if not paper_root.exists():
        return {
            "status": "ok",
            "available": False,
            "root_dir": str(paper_root),
            "message": "No paper session root found yet.",
            "generated_at": None,
            "stale_after_minutes": DEFAULT_PAPER_STALE_MINUTES,
            "total_sessions": 0,
            "status_counts": {},
            "running_sessions": [],
            "alert_status": "ok",
            "has_alerts": False,
            "alert_counts": {},
            "latest_success_session_id": None,
            "latest_success_at": None,
            "latest_alert_session_id": None,
            "latest_alert_code": None,
            "latest_alert_at": None,
            "alerts": [],
        }, 200

    try:
        payload = build_paper_sessions_alerts(paper_root)
        payload["status"] = "ok"
        payload["available"] = True
        return payload, 200
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "available": False,
            "root_dir": str(paper_root),
            "message": str(exc),
        }, 500


def build_broker_health_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    broker_root = root / "outputs" / "broker_order_validations"

    if not broker_root.exists():
        return {
            "status": "ok",
            "available": False,
            "root_dir": str(broker_root),
            "message": "No broker order-validation root found yet.",
            "total_sessions": 0,
            "approved_sessions": 0,
            "submit_gate_sessions": 0,
            "submit_response_sessions": 0,
            "submitted_sessions": 0,
            "order_status_known_sessions": 0,
            "status_counts": {},
            "submit_state_counts": {},
            "order_state_counts": {},
            "latest_submit_session_id": None,
            "latest_submit_state": None,
            "latest_order_state": None,
            "latest_submit_at": None,
            "latest_issue_session_id": None,
            "latest_issue_code": None,
            "latest_issue_at": None,
            "alert_status": "ok",
            "has_alerts": False,
            "alert_counts": {},
            "alerts": [],
        }, 200

    try:
        health = build_broker_submission_health(broker_root)
        alerts = build_broker_submission_alerts(broker_root)
        return {
            **health,
            "status": "ok",
            "available": True,
            "alert_status": alerts.get("alert_status", "ok"),
            "has_alerts": alerts.get("has_alerts", False),
            "alert_counts": alerts.get("alert_counts", {}),
            "alerts": alerts.get("alerts", []),
        }, 200
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "available": False,
            "root_dir": str(broker_root),
            "message": str(exc),
        }, 500


def build_hyperliquid_surface_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    submit_root = root / "outputs" / "hyperliquid_submits"
    search_roots = [
        root / "outputs",
        root / "tmp",
        root.parent / "tmp",
    ]

    surfaces = {
        "preflight": {
            "implemented": True,
            "artifact_name": "broker_preflight.json",
            "summary_key": "market_supported",
        },
        "account_readiness": {
            "implemented": True,
            "artifact_name": "hyperliquid_account_readiness.json",
            "summary_key": "readiness_allowed",
        },
        "signed_action": {
            "implemented": True,
            "artifact_name": "hyperliquid_signed_action.json",
            "summary_key": "readiness_allowed",
        },
        "submit_response": {
            "implemented": True,
            "artifact_name": "hyperliquid_submit_response.json",
            "summary_key": "submit_state",
        },
        "order_status": {
            "implemented": True,
            "artifact_name": "hyperliquid_order_status.json",
            "summary_key": "normalized_state",
        },
        "continuous_supervision": {
            "implemented": True,
            "artifact_name": "hyperliquid_supervision.json",
            "summary_key": "supervision_state",
        },
    }

    latest_artifacts: dict[str, dict[str, object] | None] = {}
    for key, spec in surfaces.items():
        latest_artifacts[key] = _find_latest_hyperliquid_artifact(
            search_roots,
            spec["artifact_name"],
        )

    latest_ready_artifact = next(
        (
            artifact
            for artifact in (
                latest_artifacts["continuous_supervision"],
                latest_artifacts["order_status"],
                latest_artifacts["submit_response"],
                latest_artifacts["signed_action"],
                latest_artifacts["account_readiness"],
                latest_artifacts["preflight"],
            )
            if artifact
        ),
        None,
    )

    if submit_root.exists():
        try:
            submit_health = build_hyperliquid_submission_health(submit_root)
            submit_alerts = build_hyperliquid_submission_alerts(submit_root)
        except Exception as exc:  # noqa: BLE001
            submit_health = {
                "root_dir": str(submit_root),
                "message": str(exc),
                "total_sessions": 0,
                "submit_response_sessions": 0,
                "supervision_sessions": 0,
                "submitted_sessions": 0,
                "order_status_known_sessions": 0,
                "status_counts": {},
                "submit_state_counts": {},
                "order_state_counts": {},
                "latest_submit_session_id": None,
                "latest_submit_state": None,
                "latest_order_state": None,
                "latest_submit_at": None,
                "latest_issue_session_id": None,
                "latest_issue_code": None,
                "latest_issue_at": None,
            }
            submit_alerts = {
                "root_dir": str(submit_root),
                "message": str(exc),
                "generated_at": None,
                "total_sessions": 0,
                "submit_response_sessions": 0,
                "supervision_sessions": 0,
                "submitted_sessions": 0,
                "order_state_counts": {},
                "alert_status": "error",
                "has_alerts": False,
                "alert_counts": {},
                "latest_alert_session_id": None,
                "latest_alert_code": None,
                "latest_alert_at": None,
                "alerts": [],
            }
    else:
        submit_health = {
            "root_dir": str(submit_root),
            "message": "No Hyperliquid submit root found yet.",
            "total_sessions": 0,
            "submit_response_sessions": 0,
            "supervision_sessions": 0,
            "submitted_sessions": 0,
            "order_status_known_sessions": 0,
            "status_counts": {},
            "submit_state_counts": {},
            "order_state_counts": {},
            "latest_submit_session_id": None,
            "latest_submit_state": None,
            "latest_order_state": None,
            "latest_submit_at": None,
            "latest_issue_session_id": None,
            "latest_issue_code": None,
            "latest_issue_at": None,
        }
        submit_alerts = {
            "root_dir": str(submit_root),
            "generated_at": None,
            "total_sessions": 0,
            "submit_response_sessions": 0,
            "supervision_sessions": 0,
            "submitted_sessions": 0,
            "order_state_counts": {},
            "alert_status": "ok",
            "has_alerts": False,
            "alert_counts": {},
            "latest_alert_session_id": None,
            "latest_alert_code": None,
            "latest_alert_at": None,
            "alerts": [],
        }

    return {
        "status": "ok",
        "available": True,
        "message": "Hyperliquid now spans venue preflight, signer readiness, local signing, supervised submit, and bounded post-submit supervision.",
        "search_roots": [str(path) for path in search_roots if path.exists()],
        "implemented_surfaces": {
            "preflight": True,
            "account_readiness": True,
            "signed_action_build": True,
            "cryptographic_signing": True,
            "order_submit": True,
            "submit_sessions": True,
            "post_submit_status": True,
            "continuous_supervision": True,
            "submission_health": True,
        },
        "execution_context_pressure": {
            "signer_identity": True,
            "routing_target": True,
            "transport_preference": True,
            "nonce_hint": True,
            "expires_after": True,
        },
        "submit_sessions_available": submit_root.exists(),
        "submit_sessions_root": str(submit_root),
        "submit_health": submit_health,
        "submit_alert_status": submit_alerts.get("alert_status", "ok"),
        "submit_has_alerts": submit_alerts.get("has_alerts", False),
        "submit_alert_counts": submit_alerts.get("alert_counts", {}),
        "submit_alerts": submit_alerts.get("alerts", []),
        "latest_artifacts": latest_artifacts,
        "latest_ready_artifact_type": latest_ready_artifact.get("artifact_type") if latest_ready_artifact else None,
        "latest_ready_generated_at": latest_ready_artifact.get("generated_at") if latest_ready_artifact else None,
        "signature_state": (
            latest_artifacts["signed_action"].get("signature_state")
            if latest_artifacts["signed_action"]
            else "pending_local_artifact"
        ),
    }, 200


def build_pretrade_handoff_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    pretrade_root = root / "outputs" / "pretrade_handoff"

    base_payload = {
        "status": "ok",
        "available": pretrade_root.exists(),
        "has_validation": False,
        "root_dir": str(pretrade_root),
        "surface_model": "read_only_validation_intake",
        "planner_surface": "external_calculator",
        "boundary_note": (
            "The calculator proposes. QuantLab validates, decides, and executes. "
            "This panel remains read-only."
        ),
        "message": None,
    }

    if not pretrade_root.exists():
        return {
            **base_payload,
            "message": "No pre-trade handoff validation root found yet.",
            "latest_validation_path": None,
            "latest_validation_href": None,
            "source_artifact_path": None,
            "source_artifact_href": None,
            "validation_state": "empty",
            "accepted": None,
            "reasons": [],
            "handoff_id": None,
            "symbol": None,
            "venue": None,
            "side": None,
            "planner": None,
            "ready_for_draft_execution_intent": None,
            "hinted_ready_for_draft_execution_intent": None,
            "missing_fields": [],
            "generated_at": None,
        }, 200

    latest_validation = _find_latest_pretrade_validation(pretrade_root, root)
    if latest_validation is None:
        return {
            **base_payload,
            "available": True,
            "message": "No pre-trade handoff validation artifact has been persisted yet.",
            "latest_validation_path": None,
            "latest_validation_href": None,
            "source_artifact_path": None,
            "source_artifact_href": None,
            "validation_state": "empty",
            "accepted": None,
            "reasons": [],
            "handoff_id": None,
            "symbol": None,
            "venue": None,
            "side": None,
            "planner": None,
            "ready_for_draft_execution_intent": None,
            "hinted_ready_for_draft_execution_intent": None,
            "missing_fields": [],
            "generated_at": None,
        }, 200

    payload = latest_validation["payload"]
    return {
        **base_payload,
        "available": True,
        "has_validation": True,
        "message": "Latest bounded pre-trade handoff validation loaded from local QuantLab artifacts.",
        "latest_validation_path": latest_validation["path"],
        "latest_validation_href": latest_validation["href"],
        "source_artifact_path": payload.get("source_artifact_path"),
        "source_artifact_href": _build_local_artifact_href(payload.get("source_artifact_path"), root),
        "validation_state": "accepted" if payload.get("accepted") else "rejected",
        "accepted": bool(payload.get("accepted")),
        "reasons": payload.get("reasons") if isinstance(payload.get("reasons"), list) else [],
        "handoff_id": payload.get("handoff_contract", {}).get("handoff_id"),
        "handoff_generated_at": payload.get("handoff_contract", {}).get("generated_at"),
        "handoff_contract_type": payload.get("handoff_contract", {}).get("contract_type"),
        "handoff_contract_version": payload.get("handoff_contract", {}).get("contract_version"),
        "symbol": payload.get("pretrade_context", {}).get("symbol"),
        "venue": payload.get("pretrade_context", {}).get("venue"),
        "side": payload.get("pretrade_context", {}).get("side"),
        "planner": payload.get("source", {}).get("planner"),
        "ready_for_draft_execution_intent": payload.get("quantlab_boundary", {}).get(
            "ready_for_draft_execution_intent"
        ),
        "hinted_ready_for_draft_execution_intent": payload.get("quantlab_hints", {}).get(
            "ready_for_draft_execution_intent"
        ),
        "missing_fields": payload.get("quantlab_hints", {}).get("missing_fields", []),
        "generated_at": payload.get("generated_at"),
        "policy_owner": payload.get("quantlab_boundary", {}).get("policy_owner"),
        "execution_authority": payload.get("quantlab_boundary", {}).get("execution_authority"),
        "submit_authority": payload.get("quantlab_boundary", {}).get("submit_authority"),
        "quantlab_boundary_note": payload.get("quantlab_hints", {}).get("boundary_note"),
    }, 200


def build_stepbit_workspace_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    workspace_root = root.parent
    app_repo = workspace_root / "stepbit-app"
    core_repo = workspace_root / "stepbit-core"
    live_urls = _detect_stepbit_live_urls()
    start_support = _build_stepbit_start_support(app_repo, live_urls)
    start_state = _get_stepbit_start_state(live_urls)

    app_summary = _build_workspace_repo_summary(app_repo, "control_plane")
    core_summary = _build_workspace_repo_summary(core_repo, "runtime_core")
    app_surfaces = _build_stepbit_app_surfaces(app_repo)
    app_surface_groups = _group_stepbit_entries(
        app_surfaces,
        {
            "Workspace": "Local-first user workflows and operator-facing product pages.",
            "Data": "Database-backed exploration and query-oriented utilities.",
            "Tooling": "Tool discovery and execution surfaces attached to the runtime.",
            "Automation": "Planner, pipelines, jobs, triggers, and reactive flows.",
            "Operations": "Health, runtime, and execution-history visibility.",
        },
    )
    core_capabilities = _build_stepbit_core_capabilities(core_repo)
    core_capability_groups = _group_stepbit_entries(
        core_capabilities,
        {
            "Runtime": "Low-level runtime, inference, admission, and scheduling capabilities.",
            "Reasoning": "Goal planning, reasoning graphs, and plan translation.",
            "Automation": "Pipelines, cron jobs, and event-driven orchestration.",
            "Tooling": "MCP providers and tool-execution substrate.",
            "Operations": "Readiness, observability, and distributed execution hooks.",
        },
    )
    compatibility_surfaces = _build_stepbit_compatibility_surfaces(core_repo)
    connected = app_summary["present"] and core_summary["present"]

    return {
        "status": "ok",
        "available": connected,
        "workspace_root": str(workspace_root),
        "connection_mode": "workspace_boundary" if connected else "workspace_incomplete",
        "boundary_note": "Stepbit remains an external connected surface. QuantLab stays sovereign over runtime and execution safety.",
        "live_preview_url": live_urls["preferred_url"],
        "live_urls": live_urls,
        "start_support": start_support,
        "start_state": start_state,
        "repos": {
            "stepbit_app": app_summary,
            "stepbit_core": core_summary,
        },
        "surface_model": {
            "quantlab_role": "execution_and_research_sovereign",
            "stepbit_app_role": "control_plane",
            "stepbit_core_role": "reasoning_runtime",
        },
        "workspace_summary": {
            "app_surfaces_present": sum(1 for surface in app_surfaces if surface["present"]),
            "app_surfaces_total": len(app_surfaces),
            "core_capabilities_present": sum(1 for capability in core_capabilities if capability["present"]),
            "core_capabilities_total": len(core_capabilities),
            "compatibility_surfaces_total": len(compatibility_surfaces),
            "automation_surfaces_present": sum(
                1 for surface in app_surfaces if surface["present"] and surface["category"] == "Automation"
            ),
        },
        "app_surfaces": app_surfaces,
        "app_surface_groups": app_surface_groups,
        "core_capabilities": core_capabilities,
        "core_capability_groups": core_capability_groups,
        "compatibility_surfaces": compatibility_surfaces,
    }, 200


def build_meta_trade_workspace_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    repo = _resolve_meta_trade_repo(root)
    repo_summary = _build_workspace_repo_summary(repo, "pretrade_workbench")
    product_surfaces = _build_meta_trade_entries(repo, META_TRADE_PRODUCT_SURFACE_SPECS)
    product_surface_groups = _group_stepbit_entries(
        product_surfaces,
        {
            "Workspace": "Operator-facing planning surfaces that stay upstream of QuantLab.",
            "Exports": "Deterministic serialization and bounded handoff generation.",
            "Analysis": "Auxiliary analytical surfaces that support pre-trade work.",
        },
    )
    engine_modules = _build_meta_trade_entries(repo, META_TRADE_ENGINE_MODULE_SPECS)
    engine_module_groups = _group_stepbit_entries(
        engine_modules,
        {
            "Core": "Canonical trade-plan generation and deterministic data structures.",
            "Browser": "Bounded browser modules for the workbench UI.",
            "CLI": "Headless workflow for reproducible trade-plan and handoff generation.",
            "Parity": "Cross-runtime C++ surfaces used for validation and drift control.",
        },
    )
    validation_surfaces = _build_meta_trade_entries(repo, META_TRADE_VALIDATION_SURFACES)
    validation_surface_groups = _group_stepbit_entries(
        validation_surfaces,
        {
            "Tests": "Local verification flows for browser, core, and headless paths.",
            "Parity": "Cross-runtime checks to keep JavaScript and C++ aligned.",
            "CI": "Automation that enforces contract and parity confidence.",
        },
    )
    contract_artifacts = _build_meta_trade_entries(repo, META_TRADE_CONTRACT_ARTIFACTS)
    contract_artifact_groups = _group_stepbit_entries(
        contract_artifacts,
        {
            "Docs": "Boundary and roadmap documents for the bounded upstream role.",
            "Examples": "Runnable examples for deterministic handoff generation.",
            "Fixtures": "Canonical artifacts consumed by validation and contract tests.",
        },
    )
    package_scripts = _read_package_scripts(repo)

    return {
        "status": "ok",
        "available": bool(repo_summary["present"]),
        "workspace_root": str(repo.parent),
        "boundary_mode": "upstream_pretrade_workbench" if repo_summary["present"] else "missing",
        "live_preview_url": "http://127.0.0.1:4173/",
        "boundary_note": (
            "meta_trade remains an upstream pre-trade workbench. It plans and exports "
            "deterministic artifacts. QuantLab validates, decides, and executes."
        ),
        "repo": repo_summary,
        "workspace_summary": {
            "product_surfaces_present": sum(1 for surface in product_surfaces if surface["present"]),
            "product_surfaces_total": len(product_surfaces),
            "engine_modules_present": sum(1 for module in engine_modules if module["present"]),
            "engine_modules_total": len(engine_modules),
            "validation_surfaces_present": sum(1 for surface in validation_surfaces if surface["present"]),
            "validation_surfaces_total": len(validation_surfaces),
            "contract_artifacts_present": sum(1 for artifact in contract_artifacts if artifact["present"]),
            "contract_artifacts_total": len(contract_artifacts),
            "package_script_total": len(package_scripts),
        },
        "product_surfaces": product_surfaces,
        "product_surface_groups": product_surface_groups,
        "engine_modules": engine_modules,
        "engine_module_groups": engine_module_groups,
        "validation_surfaces": validation_surfaces,
        "validation_surface_groups": validation_surface_groups,
        "contract_artifacts": contract_artifacts,
        "contract_artifact_groups": contract_artifact_groups,
        "package_scripts": package_scripts,
    }, 200


def build_launch_control_payload(project_root: Path | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    jobs = _snapshot_launch_jobs(root)
    return {
        "status": "ok",
        "available": True,
        "launcher_root": str(root / "outputs" / "research_ui" / "launches"),
        "python_path": str(_resolve_quantlab_python(root)),
        "supported_commands": ["run", "sweep"],
        "supported_run_fields": ["ticker", "start", "end", "interval", "paper", "initial_cash"],
        "supported_sweep_fields": ["config_path", "out_dir"],
        "jobs": jobs,
    }, 200


def start_stepbit_workspace(project_root: Path | None = None, request_body: dict[str, object] | None = None) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    workspace_root = root.parent
    app_repo = workspace_root / "stepbit-app"
    web_repo = app_repo / "web"

    if not app_repo.exists():
        return {
            "status": "error",
            "message": "stepbit-app repository is missing.",
        }, 404

    logs_root = root / "outputs" / "research_ui" / "stepbit"
    logs_root.mkdir(parents=True, exist_ok=True)
    live_urls = _detect_stepbit_live_urls()
    start_support = _build_stepbit_start_support(app_repo, live_urls)
    actions: list[str] = []

    with STEPBIT_START_LOCK:
        current_start_state = _get_stepbit_start_state_unlocked(live_urls)
        if current_start_state["status"] == "starting":
            return {
                "status": "accepted",
                "message": "Stepbit AI is already starting. Wait a few seconds before retrying.",
                "actions": current_start_state["actions"],
                "live_urls": live_urls,
                "logs_root": str(logs_root),
            }, 202
        _set_stepbit_start_state_unlocked("starting", current_start_state.get("actions") or [])

    if not live_urls["backend_reachable"]:
        if not start_support["can_start_backend"]:
            _set_stepbit_start_state("idle", [])
            return {
                "status": "error",
                "message": "Go is not available, so QuantLab cannot auto-start the Stepbit backend.",
            }, 400
        backend_binary = _stepbit_backend_binary_path(root)
        completed = _run_hidden_command(
            _build_stepbit_backend_build_command(backend_binary),
            cwd=app_repo,
            stdout_path=logs_root / "backend.build.stdout.log",
            stderr_path=logs_root / "backend.build.stderr.log",
            timeout_seconds=900,
        )
        if completed.returncode != 0 or not backend_binary.exists():
            _set_stepbit_start_state("idle", [])
            return {
                "status": "error",
                "message": "Stepbit backend could not be built.",
                "build_exit_code": completed.returncode,
                "stderr_log": str(logs_root / "backend.build.stderr.log"),
            }, 500
        actions.append("backend build complete")
        _set_stepbit_start_state("starting", actions)
        backend_pid = _spawn_detached_process(
            [str(backend_binary)],
            cwd=app_repo,
            stdout_path=logs_root / "backend.stdout.log",
            stderr_path=logs_root / "backend.stderr.log",
        )
        actions.append(f"backend pid {backend_pid}")
        _set_stepbit_start_state("starting", actions)
        if not _wait_for_stepbit_backend():
            _set_stepbit_start_state("idle", [])
            return {
                "status": "error",
                "message": "Stepbit backend did not become healthy in time, so the frontend was not opened.",
                "stderr_log": str(logs_root / "backend.stderr.log"),
            }, 500
        live_urls = _detect_stepbit_live_urls()
        start_support = _build_stepbit_start_support(app_repo, live_urls)

    if not live_urls["frontend_reachable"]:
        if not start_support["can_start_frontend"]:
            _set_stepbit_start_state("idle", actions)
            return {
                "status": "error",
                "message": "corepack or pnpm is not available, so QuantLab cannot auto-start the Stepbit frontend.",
            }, 400
        if start_support["frontend_install_required"]:
            install_command = _build_stepbit_frontend_install_command(web_repo)
            completed = _run_hidden_command(
                install_command,
                cwd=web_repo,
                stdout_path=logs_root / "frontend.install.stdout.log",
                stderr_path=logs_root / "frontend.install.stderr.log",
                timeout_seconds=900,
            )
            if completed.returncode != 0:
                _set_stepbit_start_state("idle", actions)
                return {
                    "status": "error",
                    "message": "Stepbit frontend dependencies could not be installed.",
                    "install_exit_code": completed.returncode,
                    "stderr_log": str(logs_root / "frontend.install.stderr.log"),
                }, 500
            actions.append("frontend install complete")
            _set_stepbit_start_state("starting", actions)

        frontend_command = _build_stepbit_frontend_start_command(web_repo)
        frontend_pid = _spawn_detached_process(
            frontend_command,
            cwd=web_repo,
            stdout_path=logs_root / "frontend.stdout.log",
            stderr_path=logs_root / "frontend.stderr.log",
            env_overrides={
                "VITE_API_BASE_URL": "http://127.0.0.1:8080/api",
                "VITE_WS_BASE_URL": "ws://127.0.0.1:8080",
            },
        )
        actions.append(f"frontend pid {frontend_pid}")

    refreshed = _detect_stepbit_live_urls()
    if not actions:
        _set_stepbit_start_state("running", [])
        return {
            "status": "ok",
            "message": "Stepbit AI is already running.",
            "live_urls": refreshed,
        }, 200

    _set_stepbit_start_state("starting", actions)

    return {
        "status": "accepted",
        "message": "Stepbit AI launch requested. The workspace may need a few seconds to become reachable.",
        "actions": actions,
        "live_urls": refreshed,
        "logs_root": str(logs_root),
    }, 202


def launch_quantlab_job(project_root: Path, request_body: dict[str, object]) -> tuple[dict, int]:
    root = Path(project_root or PROJECT_ROOT)
    request_payload = _normalize_launch_request(request_body)
    request_id = request_payload["request_id"]

    launch_dir = root / "outputs" / "research_ui" / "launches" / request_id
    launch_dir.mkdir(parents=True, exist_ok=True)
    signal_file = launch_dir / "signals.jsonl"
    stdout_file = launch_dir / "stdout.log"
    stderr_file = launch_dir / "stderr.log"

    python_path = _resolve_quantlab_python(root)
    command = [
        str(python_path),
        "main.py",
        "--json-request",
        json.dumps(request_payload, ensure_ascii=False),
        "--signal-file",
        str(signal_file),
    ]

    stdout_handle = stdout_file.open("w", encoding="utf-8")
    stderr_handle = stderr_file.open("w", encoding="utf-8")
    try:
        process = subprocess.Popen(
            command,
            cwd=root,
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
        )
    finally:
        stdout_handle.close()
        stderr_handle.close()

    job = {
        "request_id": request_id,
        "command": request_payload["command"],
        "params": request_payload["params"],
        "status": "running",
        "started_at": _utc_now_iso(),
        "ended_at": None,
        "pid": process.pid,
        "process": process,
        "signal_file": str(signal_file),
        "stdout_path": str(stdout_file),
        "stderr_path": str(stderr_file),
        "artifacts_path": None,
        "report_path": None,
        "run_id": None,
        "error_message": None,
        "exit_code": None,
    }

    with LAUNCH_LOCK:
        LAUNCH_JOBS.insert(0, job)
        del LAUNCH_JOBS[LAUNCH_HISTORY_LIMIT:]

    snapshot = _serialize_launch_job(root, job)
    return {
        "status": "accepted",
        "message": f"{request_payload['command']} launch started.",
        "job": snapshot,
    }, 202


def _normalize_launch_request(request_body: dict[str, object]) -> dict[str, object]:
    command = str(request_body.get("command") or "").strip().lower()
    if command not in {"run", "sweep"}:
        raise ValueError("Only run and sweep are supported from the dashboard launcher.")

    raw_params = request_body.get("params") or {}
    if not isinstance(raw_params, dict):
        raise ValueError("Launcher params must be a JSON object.")

    request_id = str(request_body.get("request_id") or "").strip() or f"req_ui_{uuid4().hex[:12]}"

    if command == "run":
        ticker = str(raw_params.get("ticker") or "").strip()
        start = str(raw_params.get("start") or "").strip()
        end = str(raw_params.get("end") or "").strip()
        if not ticker or not start or not end:
            raise ValueError("Run launches require ticker, start, and end.")

        params: dict[str, object] = {
            "ticker": ticker,
            "start": start,
            "end": end,
        }
        interval = str(raw_params.get("interval") or "").strip()
        if interval:
            params["interval"] = interval
        if "paper" in raw_params:
            params["paper"] = bool(raw_params.get("paper"))
        initial_cash = raw_params.get("initial_cash")
        if initial_cash not in {None, ""}:
            params["initial_cash"] = float(initial_cash)
    else:
        config_path = str(raw_params.get("config_path") or raw_params.get("sweep") or "").strip()
        if not config_path:
            raise ValueError("Sweep launches require config_path.")
        params = {"config_path": config_path}
        out_dir = str(raw_params.get("out_dir") or raw_params.get("sweep_outdir") or "").strip()
        if out_dir:
            params["out_dir"] = out_dir

    return {
        "schema_version": "1.0",
        "request_id": request_id,
        "command": command,
        "params": params,
    }


def _snapshot_launch_jobs(project_root: Path) -> list[dict[str, object]]:
    root = Path(project_root or PROJECT_ROOT)
    with LAUNCH_LOCK:
        jobs = list(LAUNCH_JOBS)

    snapshots: list[dict[str, object]] = []
    for job in jobs:
        _refresh_launch_job(root, job)
        snapshots.append(_serialize_launch_job(root, job))
    return snapshots


def _refresh_launch_job(project_root: Path, job: dict[str, object]) -> None:
    process = job.get("process")
    if process is not None and getattr(process, "poll", None):
        exit_code = process.poll()
        if exit_code is None:
            return
        job["exit_code"] = exit_code

    if job.get("status") != "running":
        return

    signals = _read_signal_events(Path(str(job["signal_file"])))
    completed_event = next((event for event in reversed(signals) if event.get("event") == "SESSION_COMPLETED"), None)
    failed_event = next((event for event in reversed(signals) if event.get("event") == "SESSION_FAILED"), None)

    if completed_event:
        job["status"] = "succeeded"
        job["ended_at"] = completed_event.get("timestamp") or _utc_now_iso()
        job["run_id"] = completed_event.get("run_id")
        job["artifacts_path"] = completed_event.get("artifacts_path")
        job["report_path"] = completed_event.get("report_path")
        return

    if failed_event:
        job["status"] = "failed"
        job["ended_at"] = failed_event.get("timestamp") or _utc_now_iso()
        job["error_message"] = failed_event.get("message") or failed_event.get("error_type")
        job["run_id"] = failed_event.get("run_id")
        return

    if job.get("exit_code") is not None:
        job["status"] = "succeeded" if job["exit_code"] == 0 else "failed"
        job["ended_at"] = _utc_now_iso()
        if job["status"] == "failed" and not job.get("error_message"):
            stderr_tail = _tail_text_file(Path(str(job["stderr_path"])), max_chars=600)
            job["error_message"] = stderr_tail or f"QuantLab exited with code {job['exit_code']}."


def _serialize_launch_job(project_root: Path, job: dict[str, object]) -> dict[str, object]:
    root = Path(project_root or PROJECT_ROOT)
    status = str(job.get("status") or "unknown")
    artifacts_href = _project_relative_href(root, job.get("artifacts_path"))
    report_href = _project_relative_href(root, job.get("report_path"))
    stdout_href = _project_relative_href(root, job.get("stdout_path"))
    stderr_href = _project_relative_href(root, job.get("stderr_path"))
    summary = _summarize_launch_params(str(job.get("command") or ""), job.get("params") or {})

    return {
        "request_id": job.get("request_id"),
        "command": job.get("command"),
        "params": job.get("params"),
        "summary": summary,
        "status": status,
        "started_at": job.get("started_at"),
        "ended_at": job.get("ended_at"),
        "pid": job.get("pid"),
        "run_id": job.get("run_id"),
        "artifacts_path": job.get("artifacts_path"),
        "artifacts_href": artifacts_href,
        "report_path": job.get("report_path"),
        "report_href": report_href,
        "stdout_href": stdout_href,
        "stderr_href": stderr_href,
        "exit_code": job.get("exit_code"),
        "error_message": job.get("error_message"),
    }


def _summarize_launch_params(command: str, params: dict[str, object]) -> str:
    if command == "run":
        ticker = params.get("ticker") or "-"
        start = params.get("start") or "-"
        end = params.get("end") or "-"
        suffix = " · paper" if params.get("paper") else ""
        return f"{ticker} · {start} -> {end}{suffix}"
    config_path = params.get("config_path") or params.get("sweep") or "-"
    return f"Config {config_path}"


def _resolve_quantlab_python(project_root: Path) -> Path:
    root = Path(project_root or PROJECT_ROOT)
    candidates = [
        root / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "bin" / "python",
        Path(sys.executable),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path(sys.executable)


def _read_signal_events(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []

    events: list[dict[str, object]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                events.append(payload)
    except OSError:
        return []
    return events


def _tail_text_file(path: Path, max_chars: int = 400) -> str:
    if not path.exists():
        return ""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    content = content.strip()
    return content[-max_chars:] if content else ""


def _project_relative_href(project_root: Path, maybe_path: object) -> str | None:
    if not maybe_path:
        return None
    path = Path(str(maybe_path))
    try:
        relative = path.resolve().relative_to(Path(project_root).resolve())
    except Exception:  # noqa: BLE001
        return None
    return "/" + str(relative).replace("\\", "/")


def _detect_stepbit_live_urls() -> dict[str, object]:
    frontend_url = _first_reachable_url(STEPBIT_FRONTEND_URLS)
    backend_url = _first_reachable_url([f"{url.rstrip('/')}/api/health" for url in STEPBIT_BACKEND_URLS])
    core_health_url = _first_reachable_url([f"{url.rstrip('/')}/health" for url in STEPBIT_CORE_URLS])
    core_ready_url = _first_reachable_url([f"{url.rstrip('/')}/ready" for url in STEPBIT_CORE_URLS])
    backend_base = backend_url.rsplit("/api/health", 1)[0] if backend_url else STEPBIT_BACKEND_URLS[0]
    core_base = core_health_url.rsplit("/health", 1)[0] if core_health_url else STEPBIT_CORE_URLS[0]
    workspace_ready = frontend_url is not None and backend_url is not None
    preferred = frontend_url if workspace_ready else (backend_base if backend_url else STEPBIT_FRONTEND_URLS[0])
    return {
        "preferred_url": preferred,
        "frontend_url": frontend_url or STEPBIT_FRONTEND_URLS[0],
        "backend_url": backend_base,
        "core_url": core_base,
        "frontend_reachable": frontend_url is not None,
        "backend_reachable": backend_url is not None,
        "core_reachable": core_health_url is not None,
        "core_ready": core_ready_url is not None,
        "reachable": workspace_ready,
    }


def _wait_for_stepbit_backend(timeout_seconds: int = 12) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if _http_url_reachable("http://127.0.0.1:8080/api/health") or _http_url_reachable("http://localhost:8080/api/health"):
            return True
        time.sleep(0.5)
    return False


def _build_stepbit_start_support(app_repo: Path, live_urls: dict[str, object]) -> dict[str, object]:
    web_repo = app_repo / "web"
    pnpm_path = shutil.which("pnpm") or shutil.which("pnpm.cmd")
    corepack_path = shutil.which("corepack") or shutil.which("corepack.cmd")
    go_path = shutil.which("go") or shutil.which("go.exe")

    return {
        "can_start_backend": bool(go_path),
        "can_start_frontend": bool(pnpm_path or corepack_path),
        "frontend_install_required": not (web_repo / "node_modules").exists(),
        "frontend_command": "pnpm" if pnpm_path else ("corepack pnpm" if corepack_path else None),
        "frontend_install_command": "pnpm install --frozen-lockfile" if pnpm_path else ("corepack pnpm install --frozen-lockfile" if corepack_path else None),
        "backend_command": "go build ./cmd/stepbit-app + run built binary" if go_path else None,
        "frontend_running": bool(live_urls.get("frontend_reachable")),
        "backend_running": bool(live_urls.get("backend_reachable")),
    }


def _stepbit_backend_binary_path(project_root: Path) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return Path(project_root) / "outputs" / "research_ui" / "stepbit" / f"stepbit-app-runtime{suffix}"


def _build_stepbit_backend_build_command(binary_path: Path) -> list[str]:
    go_path = shutil.which("go") or shutil.which("go.exe")
    if not go_path:
        raise ValueError("Go is not available.")
    return [str(go_path), "build", "-o", str(binary_path), "./cmd/stepbit-app"]


def _build_stepbit_frontend_install_command(web_repo: Path) -> list[str]:
    pnpm_path = shutil.which("pnpm") or shutil.which("pnpm.cmd")
    if pnpm_path:
        return [str(pnpm_path), "install", "--frozen-lockfile"]

    corepack_path = shutil.which("corepack") or shutil.which("corepack.cmd")
    if corepack_path:
        return [str(corepack_path), "pnpm", "install", "--frozen-lockfile"]

    raise ValueError("Neither pnpm nor corepack is available.")


def _build_stepbit_frontend_start_command(web_repo: Path) -> list[str]:
    node_path = shutil.which("node") or shutil.which("node.exe")
    vite_bin = web_repo / "node_modules" / "vite" / "bin" / "vite.js"
    if node_path and vite_bin.exists():
        return [str(node_path), str(vite_bin), "--host", "127.0.0.1", "--port", "5173"]

    pnpm_path = shutil.which("pnpm") or shutil.which("pnpm.cmd")
    if pnpm_path:
        return [str(pnpm_path), "dev", "--host", "127.0.0.1", "--port", "5173"]

    corepack_path = shutil.which("corepack") or shutil.which("corepack.cmd")
    if corepack_path:
        return [str(corepack_path), "pnpm", "dev", "--host", "127.0.0.1", "--port", "5173"]

    raise ValueError("Neither pnpm nor corepack is available.")


def _run_hidden_command(
    command: list[str],
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: int = 600,
):
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("a", encoding="utf-8") as stdout_handle, stderr_path.open("a", encoding="utf-8") as stderr_handle:
        kwargs = {
            "cwd": cwd,
            "stdout": stdout_handle,
            "stderr": stderr_handle,
            "stdin": subprocess.DEVNULL,
            "text": True,
            "timeout": timeout_seconds,
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            kwargs["startupinfo"] = startupinfo
        return subprocess.run(command, **kwargs)


def _get_stepbit_start_state(live_urls: dict[str, object]) -> dict[str, object]:
    with STEPBIT_START_LOCK:
        return _get_stepbit_start_state_unlocked(live_urls)


def _get_stepbit_start_state_unlocked(live_urls: dict[str, object]) -> dict[str, object]:
    requested_at = float(STEPBIT_START_STATE.get("requested_at") or 0.0)
    actions = list(STEPBIT_START_STATE.get("actions") or [])

    if live_urls.get("reachable"):
        return {
            "status": "running",
            "requested_at": requested_at,
            "actions": actions,
        }

    if requested_at and (time.time() - requested_at) < 45:
        return {
            "status": "starting",
            "requested_at": requested_at,
            "actions": actions,
        }

    return {
        "status": "idle",
        "requested_at": requested_at,
        "actions": actions,
    }


def _set_stepbit_start_state(status: str, actions: list[str]) -> None:
    with STEPBIT_START_LOCK:
        _set_stepbit_start_state_unlocked(status, actions)


def _set_stepbit_start_state_unlocked(status: str, actions: list[str]) -> None:
    STEPBIT_START_STATE["status"] = status
    STEPBIT_START_STATE["requested_at"] = time.time()
    STEPBIT_START_STATE["actions"] = list(actions)


def _spawn_detached_process(
    command: list[str] | str,
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    env_overrides: dict[str, str] | None = None,
) -> int:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_handle = stdout_path.open("a", encoding="utf-8")
    stderr_handle = stderr_path.open("a", encoding="utf-8")

    kwargs = {
        "cwd": cwd,
        "stdout": stdout_handle,
        "stderr": stderr_handle,
        "stdin": subprocess.DEVNULL,
        "text": True,
    }
    if env_overrides:
        env = os.environ.copy()
        env.update(env_overrides)
        kwargs["env"] = env
    if os.name == "nt":
        kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NO_WINDOW
        )
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        kwargs["startupinfo"] = startupinfo
    else:
        kwargs["start_new_session"] = True

    try:
        process = subprocess.Popen(command, **kwargs)
    finally:
        stdout_handle.close()
        stderr_handle.close()
    return process.pid


def _first_reachable_url(candidates: list[str]) -> str | None:
    for candidate in candidates:
        if _http_url_reachable(candidate):
            return candidate
    return None


def _http_url_reachable(url: str) -> bool:
    request = Request(url, method="GET", headers={"User-Agent": "QuantLab-Research-UI"})
    try:
        with urlopen(request, timeout=0.35) as response:
            return 200 <= getattr(response, "status", 200) < 500
    except HTTPError as exc:
        return 200 <= exc.code < 500
    except (TimeoutError, URLError, OSError):
        return False


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _build_workspace_repo_summary(path: Path, role: str) -> dict[str, object]:
    summary: dict[str, object] = {
        "present": path.exists() and path.is_dir(),
        "role": role,
        "path": str(path),
        "branch": None,
        "dirty": None,
        "headline": None,
    }
    if not summary["present"]:
        return summary

    branch, dirty = _read_git_branch_state(path)
    summary["branch"] = branch
    summary["dirty"] = dirty
    summary["headline"] = _read_readme_headline(path)
    return summary


def _build_stepbit_app_surfaces(app_repo: Path) -> list[dict[str, object]]:
    surfaces: list[dict[str, object]] = []
    for spec in STEPBIT_APP_SURFACE_SPECS:
        target = app_repo / spec["file"]
        surfaces.append(
            {
                **spec,
                "present": target.exists(),
                "path": str(target),
            }
        )
    return surfaces


def _build_stepbit_core_capabilities(core_repo: Path) -> list[dict[str, object]]:
    capabilities: list[dict[str, object]] = []
    for spec in STEPBIT_CORE_CAPABILITY_SPECS:
        target = core_repo / spec["path"]
        capabilities.append(
            {
                **spec,
                "present": target.exists(),
                "path": str(target),
            }
        )
    return capabilities


def _build_stepbit_compatibility_surfaces(core_repo: Path) -> list[dict[str, object]]:
    surfaces: list[dict[str, object]] = []
    api_root = core_repo / "src" / "api"
    for spec in STEPBIT_COMPATIBILITY_SURFACES:
        surfaces.append(
            {
                **spec,
                "present": api_root.exists(),
                "path_hint": str(api_root),
            }
        )
    return surfaces


def _resolve_meta_trade_repo(project_root: Path) -> Path:
    candidates = [
        project_root.parent / "meta_trade",
        project_root.parent.parent / "meta_trade",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return candidates[-1]


def _build_meta_trade_entries(repo: Path, specs: list[dict[str, str]]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for spec in specs:
        target = repo / spec["path"]
        entries.append(
            {
                **spec,
                "present": target.exists(),
                "path": str(target),
            }
        )
    return entries


def _read_package_scripts(repo: Path) -> list[dict[str, str]]:
    package_path = repo / "package.json"
    if not package_path.exists():
        return []

    try:
        payload = json.loads(package_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []

    scripts = payload.get("scripts")
    if not isinstance(scripts, dict):
        return []

    return [
        {
            "name": str(name),
            "command": str(command),
        }
        for name, command in scripts.items()
    ]


def _group_stepbit_entries(
    entries: list[dict[str, object]],
    summaries: dict[str, str],
) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for entry in entries:
        category = str(entry.get("category") or "Other")
        grouped.setdefault(category, []).append(entry)

    ordered: list[dict[str, object]] = []
    for category, items in grouped.items():
        ordered.append(
            {
                "id": category.lower().replace(" ", "_"),
                "label": category,
                "summary": summaries.get(category),
                "count": len(items),
                "present_count": sum(1 for item in items if item.get("present")),
                "items": items,
            }
        )
    ordered.sort(key=lambda group: group["label"])
    return ordered


def _read_git_branch_state(repo_path: Path) -> tuple[str | None, bool | None]:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo_path), "status", "--short", "--branch"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).splitlines()
    except Exception:  # noqa: BLE001
        return None, None

    branch = None
    if output:
        first = output[0].strip()
        if first.startswith("## "):
            branch = first[3:].split("...")[0].strip() or None
    dirty = any(line.strip() and not line.startswith("## ") for line in output)
    return branch, dirty


def _read_readme_headline(repo_path: Path) -> str | None:
    for candidate in ("README.md", "README.MD"):
        readme_path = repo_path / candidate
        if not readme_path.exists():
            continue
        try:
            for line in readme_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("# "):
                    return stripped[2:].strip()
        except Exception:  # noqa: BLE001
            return None
    return None


def _find_latest_pretrade_validation(pretrade_root: Path, project_root: Path) -> dict[str, object] | None:
    ranked: list[tuple[float, Path, dict[str, object]]] = []
    for candidate in pretrade_root.rglob(PRETRADE_HANDOFF_VALIDATION_FILENAME):
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if payload.get("artifact_type") != PRETRADE_HANDOFF_VALIDATION_CONTRACT_TYPE:
            continue
        ranked.append((candidate.stat().st_mtime, candidate, payload))

    if not ranked:
        return None

    _, path, payload = max(ranked, key=lambda item: item[0])
    return {
        "path": str(path),
        "href": _build_local_artifact_href(path, project_root),
        "payload": payload,
    }


def _build_local_artifact_href(path_value: str | Path | None, project_root: Path) -> str | None:
    if not path_value:
        return None

    try:
        path = Path(path_value).resolve()
        relative = path.relative_to(project_root.resolve())
    except Exception:  # noqa: BLE001
        return None

    return "/" + relative.as_posix()


def _find_latest_hyperliquid_artifact(search_roots: list[Path], filename: str) -> dict[str, object] | None:
    candidates: list[Path] = []
    for search_root in search_roots:
        if not search_root.exists():
            continue
        candidates.extend(search_root.rglob(filename))

    ranked: list[tuple[float, Path, dict[str, object]]] = []
    for candidate in candidates:
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not _is_hyperliquid_payload(filename, payload):
            continue
        ranked.append((candidate.stat().st_mtime, candidate, payload))

    if not ranked:
        return None

    _, path, payload = max(ranked, key=lambda item: item[0])
    return {
        "path": str(path),
        "artifact_type": payload.get("artifact_type"),
        "generated_at": payload.get("generated_at"),
        "market_supported": payload.get("market_supported"),
        "readiness_allowed": payload.get("readiness_allowed"),
        "signature_state": payload.get("signature_envelope", {}).get("signature_state"),
        "resolved_transport": payload.get("execution_context", {}).get("resolved_transport"),
        "execution_account_role": payload.get("execution_account_role"),
        "submit_state": payload.get("submit_state"),
        "submitted": payload.get("submitted"),
        "response_type": payload.get("response_type"),
        "remote_submit_called": payload.get("remote_submit_called"),
        "order_status_known": payload.get("status_known"),
        "normalized_state": payload.get("normalized_state"),
    }


def _is_hyperliquid_payload(filename: str, payload: dict[str, object]) -> bool:
    adapter_name = payload.get("adapter_name")
    if adapter_name == "hyperliquid":
        return True
    if filename == "hyperliquid_account_readiness.json":
        return "execution_account_role" in payload
    if filename == "hyperliquid_signed_action.json":
        return "signature_envelope" in payload
    if filename == "hyperliquid_submit_response.json":
        return "submit_state" in payload
    if filename == "hyperliquid_order_status.json":
        return "normalized_state" in payload or "status_known" in payload
    if filename == "hyperliquid_supervision.json":
        return "supervision_state" in payload or "polls_completed" in payload
    return False

def run_server():
    port = PORT
    max_retries = 5
    httpd = None

    while max_retries > 0:
        try:
            httpd = socketserver.TCPServer(("127.0.0.1", port), DashboardHandler)
            break
        except OSError:
            print(f"Port {port} is busy, trying {port + 1}...")
            port += 1
            max_retries -= 1

    if not httpd:
        print("Error: Could not find an available port.")
        sys.exit(1)

    print(f"\n--- QuantLab Research Dashboard Dev Server ---")
    print(f"Serving from: {PROJECT_ROOT}")
    print(f"URL: http://127.0.0.1:{port}")
    print(f"Press Ctrl+C to stop\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()
        sys.exit(0)

if __name__ == "__main__":
    run_server()
