import React, { useEffect, useState } from 'react';
import { renderPaperOpsTab } from '../modules/tab-renderers';
import { useQuantLabContext } from './QuantLabContext';

/**
 * PaperOpsPane - Native Paper Ops surface
 * 
 * Displays:
 * - Paper session health and status
 * - Broker boundary and alert management
 * - Decision queue (candidates, shortlist, baseline)
 * - Operational continuity cards ("Now / Watch / Next")
 * 
 * Renders via dangerouslySetInnerHTML (temporary bridge to existing render functions).
 * Action button wiring handled by legacy app-legacy.js event delegation.
 */
export function PaperOpsPane({ tab }) {
  const contextValue = useQuantLabContext();
  const state = contextValue?.state || {};
  const [html, setHtml] = useState('');

  useEffect(() => {
    // Build context object for renderPaperOpsTab
    const ctx = {
      snapshot: state?.snapshot || {},
      store: state?.decisionStore || {},
      decision: state?.decision || {},
      getJobs: () => state?.launchControl?.jobs || [],
      getLatestFailedJob: () => 
        (state?.launchControl?.jobs || []).find(j => j.status === 'failed'),
      getLatestRun: () => 
        (state?.runs || [])[0] || null,
      getDecisionCompareRunIds: () => 
        state?.decisionCompare?.runIds || [],
      findRun: (id) => (state?.runs || []).find(r => r.run_id === id),
    };

    try {
      const rendered = renderPaperOpsTab(ctx);
      setHtml(rendered);
    } catch (err) {
      console.error('PaperOpsPane: renderPaperOpsTab failed', err);
      setHtml(`<div class="tab-placeholder">Error rendering Paper Ops surface: ${err.message}</div>`);
    }
  }, [
    state?.snapshot,
    state?.runs,
    state?.decisionStore,
    state?.launchControl?.jobs,
    state?.decisionCompare?.runIds,
  ]);

  return (
    <div 
      className="pane-wrapper paper-ops-pane"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
