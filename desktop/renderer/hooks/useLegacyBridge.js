import { useEffect, useReducer, useCallback } from 'react';

/**
 * useLegacyBridge - Hook that provides access to the legacy app.js state
 * and allows React components to trigger updates via function calls.
 * 
 * The legacy app-legacy.js exposes functions and state in the global scope.
 * This hook provides a React-friendly interface to access and modify that state.
 * 
 * NOTE: This assumes app-legacy.js is loaded first and all legacy functions
 * are available in the global scope (not via window. prefix since they're
 * declared at top level in the script).
 * 
 * Returns: {
 *   state: LegacyState,
 *   actions: { openTab, closeTab, setBaseline, toggleCandidate, ... }
 * }
 */
export function useLegacyBridge() {
  const [renderCount, forceUpdate] = useReducer((x) => x + 1, 0);

  // Get current state from global scope (set by app-legacy.js)
  // eslint-disable-next-line no-undef
  const legacyState = typeof state !== 'undefined' ? state : null;

  // Wrapper function to call a global legacy function and trigger re-render
  const callLegacyFunction = useCallback((fnName, ...args) => {
    try {
      // eslint-disable-next-line no-undef
      if (typeof globalThis[fnName] === 'function') {
        // eslint-disable-next-line no-undef
        globalThis[fnName](...args);
      }
      // Force React to re-render after legacy function executes
      setTimeout(forceUpdate, 100);
    } catch (err) {
      console.error(`Error calling legacy function ${fnName}:`, err);
    }
  }, []);

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
        if (legacyState) {
          legacyState.activeTabId = tabId;
          // eslint-disable-next-line no-undef
          if (typeof renderTabs === 'function') {
            // eslint-disable-next-line no-undef
            renderTabs();
          }
          forceUpdate();
        }
      },
      [legacyState]
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
        if (legacyState) {
          const idx = legacyState.selectedRunIds.indexOf(runId);
          if (idx >= 0) {
            legacyState.selectedRunIds.splice(idx, 1);
          } else if (legacyState.selectedRunIds.length < 4) {
            legacyState.selectedRunIds.push(runId);
          }
          forceUpdate();
        }
      },
      [legacyState]
    ),
    setActiveTab: useCallback(
      (tabId) => callLegacyFunction('setActiveTab', tabId),
      [callLegacyFunction]
    ),
    openTab: useCallback(
      (...args) => callLegacyFunction('openTab', ...args),
      [callLegacyFunction]
    ),
    closeTab: useCallback(
      (tabId) => callLegacyFunction('closeTab', tabId),
      [callLegacyFunction]
    ),
    setBaseline: useCallback(
      (runId) => callLegacyFunction('setBaseline', runId),
      [callLegacyFunction]
    ),
  };

  // Subscribe to state changes via polling (simple approach)
  useEffect(() => {
    const interval = setInterval(() => {
      // Periodically check if state has changed
      // In a real implementation, legacy code would emit events
      forceUpdate();
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return {
    state: legacyState,
    actions,
  };
}

/**
 * Bridge data accessors that map to legacy functions
 */
export function useLegacyDataAccessors() {
  return {
    getRuns: useCallback(() => {
      // eslint-disable-next-line no-undef
      return typeof getRuns === 'function' ? getRuns() : [];
    }, []),
    
    getLatestRun: useCallback(() => {
      // eslint-disable-next-line no-undef
      return typeof getLatestRun === 'function' ? getLatestRun() : null;
    }, []),
    
    findRun: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof findRun === 'function' ? findRun(runId) : null;
    }, []),
    
    getSelectedRuns: useCallback(() => {
      // eslint-disable-next-line no-undef
      return typeof getSelectedRuns === 'function' ? getSelectedRuns() : [];
    }, []),
    
    getJobs: useCallback(() => {
      // eslint-disable-next-line no-undef
      return typeof getJobs === 'function' ? getJobs() : [];
    }, []),
    
    getLatestFailedJob: useCallback(() => {
      // eslint-disable-next-line no-undef
      return typeof getLatestFailedJob === 'function' ? getLatestFailedJob() : null;
    }, []),
    
    loadRunDetail: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof loadRunDetail === 'function' ? loadRunDetail(runId) : Promise.resolve(null);
    }, []),
    
    getRunRelatedJobs: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof getRunRelatedJobs === 'function' ? getRunRelatedJobs(runId) : [];
    }, []),
    
    getSweepDecisionEntriesForRun: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof getSweepDecisionEntriesForRun === 'function' ? getSweepDecisionEntriesForRun(runId) : [];
    }, []),
  };
}

/**
 * Bridge decision logic that wraps legacy decision functions
 */
export function useLegacyDecision() {
  return {
    isBaselineRun: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof isBaselineRun === 'function' ? isBaselineRun(runId) : false;
    }, []),
    
    isCandidateRun: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof isCandidateRun === 'function' ? isCandidateRun(runId) : false;
    }, []),
    
    isShortlistedRun: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof isShortlistedRun === 'function' ? isShortlistedRun(runId) : false;
    }, []),
    
    getCandidateEntry: useCallback((store, runId) => {
      // eslint-disable-next-line no-undef
      return typeof getCandidateEntry === 'function' ? getCandidateEntry(store, runId) : null;
    }, []),
    
    summarizeCandidateState: useCallback((store, runId) => {
      // eslint-disable-next-line no-undef
      return typeof summarizeCandidateState === 'function' ? summarizeCandidateState(store, runId) : "unknown";
    }, []),

    getCandidateEntriesResolved: useCallback(() => {
      // eslint-disable-next-line no-undef
      return typeof getCandidateEntriesResolved === 'function' ? getCandidateEntriesResolved() : [];
    }, []),
  };
}
