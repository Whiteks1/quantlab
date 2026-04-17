import { useEffect, useMemo, useState } from "react";
import styles from "./App.module.css";
import { bridge } from "./lib/bridge";
import type { WorkspaceState } from "../../shared/models/workspace";
import type { SnapshotStatus } from "../../shared/models/snapshot";
import type { RuntimeStatus } from "../../shared/models/runtime";

type SurfaceId =
  | "system"
  | "runs"
  | "compare"
  | "candidates"
  | "launch"
  | "experiments"
  | "paper-ops"
  | "assistant";

const SURFACES: Array<{ id: SurfaceId; label: string }> = [
  { id: "system", label: "System" },
  { id: "runs", label: "Runs" },
  { id: "compare", label: "Compare" },
  { id: "candidates", label: "Candidates" },
  { id: "launch", label: "Launch" },
  { id: "experiments", label: "Experiments" },
  { id: "paper-ops", label: "Paper Ops" },
  { id: "assistant", label: "Assistant" },
];

const INITIAL_WORKSPACE: WorkspaceState = {
  status: "starting",
  serverUrl: null,
  logs: [],
  error: null,
  source: null,
};

const INITIAL_SNAPSHOT: SnapshotStatus = {
  status: "idle",
  error: null,
  source: "none",
  lastSuccessAt: null,
  consecutiveErrors: 0,
  refreshPaused: false,
};

function formatWorkspaceSource(source: WorkspaceState["source"]): string {
  if (source === "managed") return "Managed";
  if (source === "external") return "External";
  return "Unknown";
}

function deriveSnapshotStatus(
  workspace: WorkspaceState,
  registryLoaded: boolean,
  registrySource: SnapshotStatus["source"],
  registryError: string | null,
): SnapshotStatus {
  if (registryError) {
    return {
      status: workspace.status === "error" ? "error" : "degraded",
      error: registryError,
      source: registrySource,
      lastSuccessAt: null,
      consecutiveErrors: 1,
      refreshPaused: false,
    };
  }

  if (!registryLoaded) {
    return INITIAL_SNAPSHOT;
  }

  return {
    status: "ok",
    error: null,
    source: registrySource,
    lastSuccessAt: new Date().toISOString(),
    consecutiveErrors: 0,
    refreshPaused: false,
  };
}

function deriveRuntimeStatus(
  workspace: WorkspaceState,
  snapshot: SnapshotStatus,
  runsIndexed: number,
): RuntimeStatus {
  return {
    workspaceStatus: workspace.status,
    workspaceSource: workspace.source,
    serverUrl: workspace.serverUrl,
    localFallbackActive: snapshot.source === "local" && runsIndexed > 0,
    runsIndexed,
    paperSessions: 0,
    brokerSessions: 0,
    stepbitAppReady: false,
    stepbitCoreReachable: false,
    stepbitCoreReady: false,
  };
}

export default function App() {
  const [activeSurface, setActiveSurface] = useState<SurfaceId>("system");
  const [workspace, setWorkspace] = useState<WorkspaceState>(INITIAL_WORKSPACE);
  const [runsIndexed, setRunsIndexed] = useState(0);
  const [registrySource, setRegistrySource] = useState<SnapshotStatus["source"]>("none");
  const [registryError, setRegistryError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  async function refreshRegistry(currentWorkspace: WorkspaceState) {
    setIsRefreshing(true);
    try {
      let registry: unknown = null;
      let source: SnapshotStatus["source"] = "none";

      if (currentWorkspace.serverUrl) {
        try {
          registry = await bridge.requestJson("/outputs/runs/runs_index.json");
          source = "api";
        } catch (_error) {
          registry = null;
        }
      }

      if (!registry) {
        registry = await bridge.readProjectJson("outputs/runs/runs_index.json");
        source = "local";
      }

      const runs = Array.isArray(registry)
        ? registry
        : Array.isArray((registry as { runs?: unknown[] })?.runs)
          ? (registry as { runs: unknown[] }).runs
          : [];

      setRunsIndexed(runs.length);
      setRegistrySource(source);
      setRegistryError(null);
    } catch (error) {
      setRunsIndexed(0);
      setRegistrySource("none");
      setRegistryError(error instanceof Error ? error.message : String(error));
    } finally {
      setIsRefreshing(false);
    }
  }

  useEffect(() => {
    let mounted = true;

    async function initialize() {
      const initialWorkspace = await bridge.getWorkspaceState();
      if (!mounted) return;
      setWorkspace(initialWorkspace);
      await refreshRegistry(initialWorkspace);
    }

    initialize().catch((error) => {
      if (!mounted) return;
      setWorkspace((current) => ({
        ...current,
        status: "error",
        error: error instanceof Error ? error.message : String(error),
      }));
    });

    const unsubscribe = bridge.onWorkspaceState((nextWorkspace) => {
      if (!mounted) return;
      setWorkspace(nextWorkspace);
      refreshRegistry(nextWorkspace).catch(() => {});
    });

    return () => {
      mounted = false;
      unsubscribe();
    };
  }, []);

  const snapshotStatus = useMemo(
    () => deriveSnapshotStatus(workspace, runsIndexed > 0 || registrySource !== "none", registrySource, registryError),
    [workspace, runsIndexed, registrySource, registryError],
  );
  const runtimeStatus = useMemo(
    () => deriveRuntimeStatus(workspace, snapshotStatus, runsIndexed),
    [workspace, snapshotStatus, runsIndexed],
  );

  const toneClass =
    workspace.status === "ready"
      ? styles.chipOk
      : workspace.status === "error"
        ? styles.chipDanger
        : styles.chipWarn;

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.sidebarTop}>
          <div className={styles.brand}>
            <p className={styles.eyebrow}>QuantLab Desktop</p>
            <h1 className={styles.title}>React runtime</h1>
            <p className={styles.subtitle}>
              Vite-backed renderer runtime. Shared IPC and model contracts remain authoritative.
            </p>
          </div>

          <section className={styles.navSection} aria-label="Desktop surfaces">
            <p className={styles.sectionLabel}>Surfaces</p>
            <nav className={styles.nav}>
              {SURFACES.map((surface) => (
                <button
                  key={surface.id}
                  type="button"
                  className={`${styles.navButton} ${activeSurface === surface.id ? styles.navButtonActive : ""}`.trim()}
                  onClick={() => setActiveSurface(surface.id)}
                >
                  {surface.label}
                </button>
              ))}
            </nav>
          </section>
        </div>

        <div className={styles.sidebarBottom}>
          <section className={styles.sidebarPanel}>
            <p className={styles.eyebrow}>Boundary</p>
            <p>
              Legacy renderer files remain in the repo, but this runtime does not mount them. Non-migrated
              surfaces stay explicitly paused instead of falling through to unsafe DOM or CSS collisions.
            </p>
          </section>
        </div>
      </aside>

      <div className={styles.main}>
        <header className={styles.topbar}>
          <div>
            <p className={styles.eyebrow}>Desktop runtime</p>
            <h2 className={styles.topbarTitle}>{SURFACES.find((surface) => surface.id === activeSurface)?.label}</h2>
          </div>
          <div className={styles.topbarMeta}>
            <span className={`${styles.chip} ${toneClass}`.trim()}>Workspace {workspace.status}</span>
            <span className={styles.chip}>Source {formatWorkspaceSource(workspace.source)}</span>
            <span className={`${styles.chip} ${snapshotStatus.status === "ok" ? styles.chipOk : styles.chipWarn}`.trim()}>
              Snapshot {snapshotStatus.status}
            </span>
          </div>
        </header>

        <main className={styles.body}>
          <section className={`${styles.card} ${styles.grid}`.trim()}>
            {activeSurface === "system" ? (
              <>
                <div>
                  <h3 className={styles.cardTitle}>System status</h3>
                  <p className={styles.cardCopy}>
                    This shell runs through Vite and React, but reads state through the existing preload and
                    shared contracts.
                  </p>
                </div>

                <div className={styles.metricGrid}>
                  <div className={styles.metric}>
                    <p className={styles.metricLabel}>Workspace</p>
                    <p className={styles.metricValue}>{runtimeStatus.workspaceStatus}</p>
                  </div>
                  <div className={styles.metric}>
                    <p className={styles.metricLabel}>Server URL</p>
                    <p className={styles.metricValue}>{runtimeStatus.serverUrl || "none"}</p>
                  </div>
                  <div className={styles.metric}>
                    <p className={styles.metricLabel}>Runs indexed</p>
                    <p className={styles.metricValue}>{runtimeStatus.runsIndexed}</p>
                  </div>
                  <div className={styles.metric}>
                    <p className={styles.metricLabel}>Snapshot source</p>
                    <p className={styles.metricValue}>{snapshotStatus.source}</p>
                  </div>
                </div>

                <div className={styles.actions}>
                  <button
                    type="button"
                    className={styles.button}
                    onClick={() => {
                      bridge.restartWorkspaceServer().catch(() => {});
                    }}
                  >
                    Restart workspace server
                  </button>
                  <button
                    type="button"
                    className={`${styles.button} ${styles.buttonSecondary}`.trim()}
                    onClick={() => {
                      bridge.openPath("outputs").catch(() => {});
                    }}
                  >
                    Open outputs
                  </button>
                  <button
                    type="button"
                    className={`${styles.button} ${styles.buttonSecondary}`.trim()}
                    onClick={() => {
                      refreshRegistry(workspace).catch(() => {});
                    }}
                  >
                    {isRefreshing ? "Refreshing..." : "Refresh snapshot"}
                  </button>
                </div>

                <div>
                  <h3 className={styles.cardTitle}>Workspace logs</h3>
                  {workspace.logs.length > 0 ? (
                    <ol className={styles.logList}>
                      {workspace.logs.slice(-8).map((line, index) => (
                        <li key={`${index}-${line}`}>{line}</li>
                      ))}
                    </ol>
                  ) : (
                    <p className={styles.cardCopy}>No workspace logs yet.</p>
                  )}
                </div>
              </>
            ) : (
              <>
                <div>
                  <h3 className={styles.cardTitle}>Surface paused</h3>
                  <p className={styles.cardCopy}>
                    {SURFACES.find((surface) => surface.id === activeSurface)?.label} is intentionally not remounted
                    in this slice. The runtime is now real and buildable; feature migration resumes on top of this
                    foundation.
                  </p>
                </div>
                <div className={styles.surfaceGrid}>
                  <div className={styles.surfaceItem}>
                    <strong>What this slice enables</strong>
                    React now runs through a real Vite build instead of browser-side JSX and bare-package imports.
                  </div>
                  <div className={styles.surfaceItem}>
                    <strong>What stays authoritative</strong>
                    `main`, `preload`, and `desktop/shared/*` remain the only contract source.
                  </div>
                  <div className={styles.surfaceItem}>
                    <strong>What stays out of scope</strong>
                    No surface logic migration, no legacy retirement, no shared-model duplication.
                  </div>
                </div>
              </>
            )}
          </section>

          <aside className={`${styles.card} ${styles.assistant}`.trim()}>
            <div>
              <p className={styles.eyebrow}>Assistant lane</p>
              <h3 className={styles.cardTitle}>Migration notes</h3>
            </div>
            <p className={styles.note}>
              Desktop remains under blocker review. This runtime slice exists to restore an executable React path
              with proper tooling before feature migration continues.
            </p>
            <p className={styles.note}>
              Shared contracts in <code>desktop/shared</code> are consumed directly; no renderer-local schemas
              are introduced here.
            </p>
            {registryError ? (
              <p className={styles.note}>Registry refresh error: {registryError}</p>
            ) : (
              <p className={styles.note}>Registry refresh status: {snapshotStatus.status} via {snapshotStatus.source}.</p>
            )}
          </aside>
        </main>
      </div>
    </div>
  );
}
