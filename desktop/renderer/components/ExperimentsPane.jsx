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
 * Renders via dangerouslySetInnerHTML (temporary bridge to existing render functions).
 * Action button wiring handled by legacy app-legacy.js event delegation.
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
      findRun: (id) => (state?.runs || []).find(r => r.run_id === id),
      findSweepDecisionRow: (id) => 
        (state?.sweepDecisionStore?.entries || []).find(e => e.entry_id === id),
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
    state?.sweepDecisionStore,
    tab?.selectedConfigPath,
  ]);

  return (
    <div 
      className="pane-wrapper experiments-pane"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
