import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
} from 'react';

/** @typedef {{ run_id: string, mode?: string, ticker?: string, created_at?: string, total_return?: number, sharpe_simple?: number, max_drawdown?: number, trades?: number, path?: string }} RunEntry */
/** @typedef {{ runsRegistry: { runs: RunEntry[] } | null, paperHealth: object | null, brokerHealth: object | null }} Snapshot */

const REFRESH_INTERVAL_MS = 15_000;
const MAX_CONSECUTIVE_ERRORS = 5;

const RegistryContext = createContext(null);

/**
 * Hook to consume the RegistryContext.
 * Returns { runs, jobs, snapshot, isLoading, lastError }.
 */
export function useRegistry() {
  const ctx = useContext(RegistryContext);
  if (!ctx) {
    throw new Error('useRegistry must be used within RegistryProvider');
  }
  return ctx;
}

/**
 * RegistryProvider — React-native data authority for the workstation.
 *
 * Responsibilities:
 *  - Load the runs index on mount and on a 15-second refresh cycle.
 *  - Attempt the server API first; fall back to `readProjectJson` (local file).
 *  - Expose `runs`, `snapshot`, and health status to the rest of the shell.
 *  - Halt the refresh loop after MAX_CONSECUTIVE_ERRORS failures.
 */
export function RegistryProvider({ children }) {
  const [runs, setRuns] = useState([]);
  const [snapshot, setSnapshot] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastError, setLastError] = useState(null);
  const consecutiveErrors = useRef(0);
  const bridge = window.quantlabDesktop;

  /**
   * Attempt to load a JSON resource.
   * Tries server API (requestJson) first, then local bridge (readProjectJson).
   * Returns the parsed object or null.
   */
  const fetchJson = useCallback(async (relativePath) => {
    const localPath = String(relativePath || '').replace(/^\/+/, '');
    const apiPath = `/${localPath}`;
    // 1. Prefer the local project file so smoke runs and offline workflows
    // can resolve the seeded runs index before consulting the live server.
    try {
      const data = await bridge.readProjectJson(localPath);
      if (data) return { data, source: 'local' };
    } catch (_localError) {
      // fall through
    }
    // 2. Try the live server endpoint.
    try {
      const data = await bridge.requestJson(apiPath);
      if (data) return { data, source: 'server' };
    } catch (_serverError) {
      // fall through
    }
    return null;
  }, []);

  /**
   * Refresh the registry snapshot: runs index + optional paper/broker health.
   */
  const refreshSnapshot = useCallback(async () => {
    try {
      const result = await fetchJson('/outputs/runs/runs_index.json');
      if (result) {
        const { data } = result;
        setRuns(Array.isArray(data?.runs) ? data.runs : []);
        setSnapshot((prev) => ({
          ...(prev || {}),
          runsRegistry: data,
        }));
        setLastError(null);
        consecutiveErrors.current = 0;
      }
    } catch (err) {
      consecutiveErrors.current += 1;
      setLastError(err?.message || 'Registry refresh failed');
      console.warn('[RegistryContext] Refresh error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [fetchJson]);

  // Initial load on mount
  useEffect(() => {
    refreshSnapshot();
  }, [refreshSnapshot]);

  // Periodic refresh loop — pauses when too many consecutive errors
  useEffect(() => {
    const interval = setInterval(() => {
      if (consecutiveErrors.current >= MAX_CONSECUTIVE_ERRORS) return;
      refreshSnapshot();
    }, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refreshSnapshot]);

  const value = {
    runs,
    snapshot,
    isLoading,
    lastError,
    refreshSnapshot,
  };

  return (
    <RegistryContext.Provider value={value}>
      {children}
    </RegistryContext.Provider>
  );
}
