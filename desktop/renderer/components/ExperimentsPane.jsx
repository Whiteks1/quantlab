import React, { useEffect, useState } from 'react';
import { renderExperimentsTab } from '../modules/tab-renderers';
import { useQuantLabContext } from './QuantLabContext';

/**
 * ExperimentsPane - Native Experiments/config workspace surface
 * 
 * Displays:
 * - Experiment config catalog
 * - Recent sweeps and leaderboards
 * - Sweep decision tracking
 * - Config launch actions
 * - Sweep file inspection
 * 
 * Renders via dangerouslySetInnerHTML as an adapter around the existing
 * renderer function while state ownership stays in React.
 */
export function ExperimentsPane({ tab }) {
  const contextValue = useQuantLabContext();
  const state = contextValue?.state || {};
  const [html, setHtml] = useState('');

  useEffect(() => {
    // Build context object for renderExperimentsTab
    const ctx = {
      experimentsWorkspace: state?.experimentsWorkspace || 
        { status: 'idle', configs: [], sweeps: [], error: null },
      sweepDecision: state?.sweepDecision || {},
      sweepDecisionStore: state?.sweepDecisionStore || {},
      findRun: contextValue?.findRun || (() => null),
      findSweepDecisionRow: (id) => {
        for (const sweep of state?.experimentsWorkspace?.sweeps || []) {
          const row = (sweep.decisionRows || []).find((entry) => entry.entry_id === id);
          if (row) return { ...row, sweep };
        }
        return null;
      },
    };

    try {
      const rendered = renderExperimentsTab(tab, ctx);
      setHtml(rendered);
    } catch (err) {
      console.error('ExperimentsPane: renderExperimentsTab failed', err);
      setHtml(`<div class="tab-placeholder">Error rendering Experiments surface: ${err.message}</div>`);
    }
  }, [
    state?.experimentsWorkspace,
    state?.sweepDecision,
    state?.sweepDecisionStore,
    contextValue?.findRun,
    tab?.selectedConfigPath,
  ]);

  return (
    <div 
      className="pane-wrapper experiments-pane"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
