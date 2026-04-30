import React, { createContext, useContext, useMemo, useState, useEffect, useCallback } from 'react';
import {
  useLegacyBridge,
  useLegacyDataAccessors,
  useLegacyDecision,
} from '../hooks/useLegacyBridge';
import { useRegistry } from './RegistryContext';
export { RegistryProvider } from './RegistryContext';

const bridge = window.quantlabDesktop;

/**
 * QuantLabContext provides access to the app state, decision logic,
 * and actions for all surface components (Runs, Compare, Candidates).
*
 * Populated by the App.jsx root component; surfaces consume it via useQuantLab().
 */
export const QuantLabContext = createContext(null);

/**
 * Hook to access QuantLab state and actions in any surface component.
 */
export function useQuantLab() {
  const context = useContext(QuantLabContext);
  if (!context) {
    throw new Error(
      'useQuantLab must be called within QuantLabContext.Provider'
    );
  }
  return context;
}

/**
 * Hook that builds the full context value by bridging to legacy state.
 * Use this in App.jsx to populate the QuantLabContext.Provider value.
 */
export function useQuantLabContextValue() {
  const { state: legacyState, actions: legacyActions } = useLegacyBridge();
  const legacyDataAccessors = useLegacyDataAccessors();
  const decision = useLegacyDecision();

  // Native registry: authoritative source of run data (#412 B.1)
  const registry = useRegistry();

  // 1. Native workstation shell state (Master)
  const [tabs, setTabs] = useState([]);
  const [activeTabId, setActiveTabId] = useState(null);
  const [selectedRunIds, setSelectedRunIds] = useState([]);
  const [isInitialized, setIsInitialized] = useState(false);

  // 2. Initialize state from persistence layer on mount
  useEffect(() => {
    async function loadInitialState() {
      try {
        const store = await bridge.getShellWorkspaceStore();
        if (store) {
          setTabs(store.tabs || []);
          setActiveTabId(store.active_tab_id || (store.tabs?.[0]?.id) || null);
          setSelectedRunIds(store.selected_run_ids || []);
        }
      } catch (err) {
        console.error('Failed to load initial workstation state:', err);
      } finally {
        setIsInitialized(true);
      }
    }
    loadInitialState();
  }, []);

  // 3. Centralized persistence: Sync to Electron whenever workstation state changes
  useEffect(() => {
    if (!isInitialized) return;

    const store = {
      version: 1,
      tabs,
      active_tab_id: activeTabId,
      selected_run_ids: selectedRunIds,
      // Note: We don't touch launch_form here yet to keep the slice narrow
    };

    bridge.saveShellWorkspaceStore(store)
      .catch(err => console.error('Failed to persist workstation state:', err));
  }, [tabs, activeTabId, selectedRunIds, isInitialized]);

  // 4. Native actions (Simplified by centralized persistence)
  const openTab = useCallback((kind, title, requestIdOrRunId) => {
    setTabs(currentTabs => {
      const existing = currentTabs.find(t =>
        (t.kind === kind && t.requestId === requestIdOrRunId) ||
        (t.kind === kind && t.runId === requestIdOrRunId)
      );

      if (existing) {
        setActiveTabId(existing.id);
        return currentTabs;
      }

      let nextId = `tab-${Date.now()}`;
      if (kind === 'run') nextId = `run:${requestIdOrRunId}`;
      if (kind === 'artifacts') nextId = `artifacts:${requestIdOrRunId}`;
      if (kind === 'job') nextId = `job:${requestIdOrRunId}`;

      const newTab = { id: nextId, kind, title: title || `${kind} review` };
      if (kind === 'job') newTab.requestId = requestIdOrRunId;
      if (kind === 'run' || kind === 'artifacts') newTab.runId = requestIdOrRunId;

      setActiveTabId(nextId);
      return [...currentTabs, newTab];
    });
  }, []);

  const closeTab = useCallback((tabId) => {
    setTabs(currentTabs => {
      const nextTabs = currentTabs.filter(t => t.id !== tabId);
      if (activeTabId === tabId) {
        setActiveTabId(nextTabs[nextTabs.length - 1]?.id || null);
      }
      return nextTabs;
    });
  }, [activeTabId]);

  const setActiveTab = useCallback((tabId) => {
    setActiveTabId(tabId);
  }, []);

  const navigateToSurface = useCallback((kind) => {
    setTabs(currentTabs => {
      // Logic for selecting the "default" ID for a kind
      // For runs, compare, candidates, paper, system, experiments, it's usually just the kind as ID
      const surfaceIdMap = {
        'runs': 'runs-native', // Match smoke test expectation
        'candidates': 'candidates',
        'compare': 'compare-selection',
        'paper-ops': 'paper-ops',
        'system': 'system',
        'experiments': 'experiments',
        'launch': 'launch'
      };

      const id = surfaceIdMap[kind] || kind;
      const existing = currentTabs.find(t => t.id === id);

      if (existing) {
        setActiveTabId(id);
        return currentTabs;
      }

      // Add new tab if missing
      const titleMap = {
        'runs': 'Runs',
        'candidates': 'Candidates',
        'compare': 'Compare',
        'paper-ops': 'Paper Ops',
        'system': 'System',
        'experiments': 'Experiments',
        'launch': 'Launch'
      };

      const newTab = { id, kind, title: titleMap[kind] || kind };
      setActiveTabId(id);
      return [...currentTabs, newTab];
    });
  }, []);

  const toggleRunSelection = useCallback((runId) => {
    setSelectedRunIds(current =>
      current.includes(runId)
        ? current.filter(id => id !== runId)
        : [...current, runId]
    );
  }, []);

  // Native data accessors — read from RegistryContext, fall back to legacy globals
  const dataAccessors = useMemo(() => ({
    getRuns: () => registry.runs,
    getLatestRun: () => registry.runs[registry.runs.length - 1] || null,
    findRun: (runId) => registry.runs.find((r) => r.run_id === runId) || null,
    getSelectedRuns: () =>
      registry.runs.filter((r) => selectedRunIds.includes(r.run_id)),
    // These still delegate to legacy globals for now
    getJobs: legacyDataAccessors.getJobs,
    getLatestFailedJob: legacyDataAccessors.getLatestFailedJob,
    loadRunDetail: legacyDataAccessors.loadRunDetail,
    getRunRelatedJobs: legacyDataAccessors.getRunRelatedJobs,
    getSweepDecisionEntriesForRun: legacyDataAccessors.getSweepDecisionEntriesForRun,
  }), [registry.runs, selectedRunIds, legacyDataAccessors]);

  // Combine native workstation state with legacy snapshot/decision data
  const value = useMemo(
    () => ({
      state: {
        ...(legacyState || {}), // Guard against null legacyState
        tabs,
        activeTabId,
        selectedRunIds,
        isInitialized,
        // Surface registry health for Topbar / smoke diagnostics
        registryLoading: registry.isLoading,
        registryError: registry.lastError,
      },
      ...dataAccessors,
      decision,
      ...legacyActions, // decision-related actions (setBaseline, etc.)
      openTab,
      closeTab,
      setActiveTab,
      navigateToSurface,
      toggleRunSelection,
    }),
    [legacyState, tabs, activeTabId, selectedRunIds, isInitialized, registry.isLoading, registry.lastError, dataAccessors, decision, legacyActions, openTab, closeTab, setActiveTab, navigateToSurface, toggleRunSelection]
  );

  return value;
}

/**
 * QuantLabContext.Provider wraps the entire app.
 * Value shape:
 * {
 *   state: {
 *     workspace: { status, serverUrl, error, logs },
 *     snapshot: { runsRegistry, launchControl, paperHealth, brokerHealth, stepbitWorkspace },
 *     candidatesStore: { baseline_run_id, candidates: [...] },
 *     selectedRunIds: string[],
 *     tabs: Tab[],
 *     activeTabId: string | null,
 *   },
*
 *   // Data accessors (mirrors legacy ctx functions)
 *   getRuns: () => Run[],
 *   getLatestRun: () => Run | null,
 *   findRun: (runId: string) => Run | null,
 *   getSelectedRuns: () => Run[],
 *   getJobs: () => Job[],
 *   getLatestFailedJob: () => Job | null,
*
 *   // Decision logic (access isCandidateRun, isShortlistedRun, etc.)
 *   decision: {
 *     isBaselineRun: (runId: string) => boolean,
 *     isCandidateRun: (runId: string) => boolean,
 *     isShortlistedRun: (runId: string) => boolean,
 *     getCandidateEntriesResolved: () => CandidateEntry[],
 *   },
 *   // Actions to modify state
 *   setBaseline: (runId: string) => void,
 *   toggleCandidate: (runId: string) => void,
 *   toggleShortlist: (runId: string) => void,
 *   openTab: (tab: Tab) => void,
 *   closeTab: (tabId: string) => void,
 *   setActiveTab: (tabId: string) => void,
 * }
 */
export const QuantLabContextProvider = ({ value, children }) => {
  return (
    <QuantLabContext.Provider value={value}>
      {children}
    </QuantLabContext.Provider>
  );
};
