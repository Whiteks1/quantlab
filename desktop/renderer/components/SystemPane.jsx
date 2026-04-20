import React, { useEffect, useState } from 'react';
import { renderSystemTab } from '../modules/tab-renderers';
import { useQuantLabContext } from './QuantLabContext';

/**
 * SystemPane - Native System/runtime diagnostics surface
 * 
 * Displays:
 * - Workspace bootstrap state (status, server URL, snapshot source)
 * - API refresh diagnostics
 * - Launch surface visibility
 * - Runtime logs and continuity
 * - Broker alert summary
 * - Paper and operational state
 * 
 * Renders via dangerouslySetInnerHTML (temporary bridge to existing render functions).
 * Action button wiring handled by legacy app-legacy.js event delegation.
 */
export function SystemPane({ tab }) {
  const contextValue = useQuantLabContext();
  const state = contextValue?.state || {};
  const [html, setHtml] = useState('');

  useEffect(() => {
    // Build context object for renderSystemTab
    const ctx = {
      workspace: state?.workspace || {},
      snapshotStatus: state?.snapshotStatus || {},
      snapshot: state?.snapshot || {},
      getRuns: () => state?.runs || [],
      getLatestRun: () => 
        (state?.runs || [])[0] || null,
      getLatestFailedJob: () => 
        (state?.launchControl?.jobs || []).find(j => j.status === 'failed'),
      decision: state?.decision || {},
      store: state?.decisionStore || {},
      findRun: (id) => (state?.runs || []).find(r => r.run_id === id),
      maxLogPreviewChars: 500,
    };

    try {
      const rendered = renderSystemTab(ctx);
      setHtml(rendered);
    } catch (err) {
      console.error('SystemPane: renderSystemTab failed', err);
      setHtml(`<div class="tab-placeholder">Error rendering System surface: ${err.message}</div>`);
    }
  }, [
    state?.workspace,
    state?.snapshotStatus,
    state?.snapshot,
    state?.runs,
  ]);

  return (
    <div 
      className="pane-wrapper system-pane"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
