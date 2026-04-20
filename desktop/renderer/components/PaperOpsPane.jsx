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
 * Renders via dangerouslySetInnerHTML as an adapter around the existing
 * renderer function while state ownership stays in React.
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
      decision: contextValue?.decision || {},
      getJobs: contextValue?.getJobs || (() => []),
      getLatestFailedJob: contextValue?.getLatestFailedJob || (() => null),
      getLatestRun: contextValue?.getLatestRun || (() => null),
      getDecisionCompareRunIds: contextValue?.decision?.getDecisionCompareRunIds || (() => []),
      findRun: contextValue?.findRun || (() => null),
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
    state?.decisionStore,
    contextValue?.decision,
    contextValue?.getJobs,
    contextValue?.getLatestFailedJob,
    contextValue?.getLatestRun,
    contextValue?.findRun,
  ]);

  return (
    <div 
      className="pane-wrapper paper-ops-pane"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
