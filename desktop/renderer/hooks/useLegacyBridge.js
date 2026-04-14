import { useEffect, useReducer, useCallback } from 'react';

/**
 * useLegacyBridge - Hook that provides access to the legacy app.js state
 * and allows React components to trigger updates that synchronize with the legacy shell.
 * 
 * This hook reads from window.state (managed by legacy app.js) and provides
 * a React-friendly interface to access and modify the state.
 * 
 * Returns: {
 *   state: LegacyState,
 *   actions: { openTab, closeTab, setBaseline, toggleCandidate, ... }
 * }
 */
export function useLegacyBridge() {
  const [, forceUpdate] = useReducer((x) => x + 1, 0);

  // Get current state from legacy app
  const legacyState = window.state || null;

  // Wrapper function to call legacy functions and trigger React re-render
  const callLegacyFunction = useCallback((fnName, ...args) => {
    if (window[fnName] && typeof window[fnName] === 'function') {
      window[fnName](...args);
      // Force React to re-render after legacy function executes
      // This is needed because the legacy app updates window.state directly
      setTimeout(forceUpdate, 0);
    }
  }, [forceUpdate]);

  // Bridge actions that map to legacy functions
  const actions = {
    openTab: useCallback(
      (tabData) => callLegacyFunction('upsertTab', tabData),
      [callLegacyFunction]
    ),
    closeTab: useCallback(
      (tabId) => callLegacyFunction('closeTab', tabId),
      [callLegacyFunction]
    ),
    setActiveTab: useCallback(
      (tabId) => {
        legacyState.activeTabId = tabId;
        callLegacyFunction('renderTabs');
      },
      [legacyState, callLegacyFunction]
    ),
    setBaseline: useCallback(
      (runId) => callLegacyFunction('setBaseline', runId),
      [callLegacyFunction]
    ),
    toggleCandidate: useCallback(
      (runId) => callLegacyFunction('toggleCandidate', runId),
      [callLegacyFunction]
    ),
    toggleShortlist: useCallback(
      (runId) => callLegacyFunction('toggleShortlist', runId),
      [callLegacyFunction]
    ),
    toggleRunSelection: useCallback(
      (runId) => {
        const idx = legacyState.selectedRunIds.indexOf(runId);
        if (idx >= 0) {
          legacyState.selectedRunIds.splice(idx, 1);
        } else if (legacyState.selectedRunIds.length < 4) {
          legacyState.selectedRunIds.push(runId);
        }
        forceUpdate();
      },
      [legacyState, forceUpdate]
    ),
  };

  // Subscribe to window-level legacy state changes
  useEffect(() => {
    const interval = setInterval(() => {
      // Poll for changes in the legacy state (simple approach)
      // Proper approach would use event emitters in legacy code
      forceUpdate();
    }, 1000);
    return () => clearInterval(interval);
  }, [forceUpdate]);

  return {
    state: legacyState,
    actions,
  };
}

/**
 * Bridge data accessors that map to legacy functions
 */
export function useLegacyDataAccessors() {
  const { state } = useLegacyBridge();

  return {
    getRuns: useCallback(
      () => window.getRuns?.() || [],
      []
    ),
    getLatestRun: useCallback(
      () => window.getLatestRun?.() || null,
      []
    ),
    findRun: useCallback(
      (runId) => window.findRun?.(runId) || null,
      []
    ),
    getSelectedRuns: useCallback(
      () => window.getSelectedRuns?.() || [],
      []
    ),
    getJobs: useCallback(
      () => window.getJobs?.() || [],
      []
    ),
    getLatestFailedJob: useCallback(
      () => window.getLatestFailedJob?.() || null,
      []
    ),
    loadRunDetail: useCallback(
      (runId) => window.loadRunDetail?.(runId),
      []
    ),
  };
}

/**
 * Bridge decision logic that wraps legacy decision functions
 */
export function useLegacyDecision() {
  return {
    isBaselineRun: useCallback(
      (runId) => window.isBaselineRun?.(runId) || false,
      []
    ),
    isCandidateRun: useCallback(
      (runId) => window.isCandidateRun?.(runId) || false,
      []
    ),
    isShortlistedRun: useCallback(
      (runId) => window.isShortlistedRun?.(runId) || false,
      []
    ),
    getCandidateEntriesResolved: useCallback(
      () => window.getCandidateEntriesResolved?.() || [],
      []
    ),
  };
}
