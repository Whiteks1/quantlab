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

  const handleSurfaceClick = (event) => {
    const target = event.target?.closest?.('[data-open-job], [data-open-run], [data-open-job-artifacts], [data-open-job-link], [data-open-external]');
    if (!target) return;

    const { openJob, openRun, openJobArtifacts, openJobLink, openExternal } = target.dataset;
    if (openJob) {
      event.preventDefault();
      contextValue?.openTab?.({ kind: 'job', requestId: openJob });
    } else if (openRun) {
      event.preventDefault();
      contextValue?.openTab?.({ kind: 'run', runId: openRun });
    } else if (openJobArtifacts) {
      event.preventDefault();
      const job = contextValue?.findJob?.(openJobArtifacts);
      if (job?.run_id) {
        contextValue?.openTab?.({ kind: 'artifacts', runId: job.run_id });
      } else if (job?.artifacts_href && typeof window.quantlabDesktop?.openExternal === 'function') {
        window.quantlabDesktop.openExternal(job.artifacts_href);
      }
    } else if (openJobLink || openExternal) {
      event.preventDefault();
      const href = openJobLink || openExternal;
      if (typeof window.quantlabDesktop?.openExternal === 'function') {
        window.quantlabDesktop.openExternal(href);
      }
    }
  };

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
      onClick={handleSurfaceClick}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
