import React, { createContext, useContext, useMemo } from 'react';
import {
  useLegacyBridge,
  useLegacyDataAccessors,
  useLegacyDecision,
} from '../hooks/useLegacyBridge';

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
  const { state, actions } = useLegacyBridge();
  const dataAccessors = useLegacyDataAccessors();
  const decision = useLegacyDecision();

  // Memoize the context value to avoid unnecessary re-renders
  const value = useMemo(
    () => ({
      state,
      ...dataAccessors,
      decision,
      ...actions,
    }),
    [state, dataAccessors, decision, actions]
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
 *   
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
