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
 * Renders via dangerouslySetInnerHTML as an adapter around the existing
 * renderer function while state ownership stays in React.
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
      getRuns: contextValue?.getRuns || (() => []),
      getLatestRun: contextValue?.getLatestRun || (() => null),
      getLatestFailedJob: contextValue?.getLatestFailedJob || (() => null),
      decision: contextValue?.decision || {},
      store: state?.decisionStore || {},
      findRun: contextValue?.findRun || (() => null),
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
    state?.decisionStore,
    contextValue?.decision,
    contextValue?.getRuns,
    contextValue?.getLatestRun,
    contextValue?.getLatestFailedJob,
    contextValue?.findRun,
  ]);

  return (
    <div 
      className="pane-wrapper system-pane"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
