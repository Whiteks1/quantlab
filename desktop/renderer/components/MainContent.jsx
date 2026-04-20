import React, { useEffect, useRef } from 'react';
import { RunsPane } from './RunsPane';
import { ComparePane } from './ComparePane';
import { CandidatesPane } from './CandidatesPane';
import { RunDetailPane } from './RunDetailPane';
import { TabsBar } from './TabsBar';
import { PaperOpsPane } from './PaperOpsPane';
import { SystemPane } from './SystemPane';

/**
 * MainContent - Main content area that:
 * - Mounts React-based surfaces (Runs, Compare, Candidates)
 * - Provides container for legacy surface HTML (other surfaces, iframes)
 * - Manages surface tab context and active tab rendering
 * 
 * Surfaces are mounted based on activeTab.kind:
 * - 'runs': RunsPane
 * - 'compare': ComparePane
 * - 'candidates': CandidatesPane
 * - Other kinds: rendered via legacy HTML or iframes
 */
export default function MainContent({ activeTab, allTabs, onTabChange }) {
  const legacyContainerRef = useRef(null);

  // Re-render legacy content when non-React tabs are active
  useEffect(() => {
    if (
      activeTab &&
      !['runs', 'compare', 'candidates', 'run', 'artifacts', 'paper', 'system'].includes(activeTab.kind)
    ) {
      // Legacy surfaces (paper, system, experiments, job, run, artifacts, iframe, etc.)
      // remain rendered by the legacy app.js via the DOM
      if (window.__quantlab?.renderLegacyTab) {
        window.__quantlab.renderLegacyTab(activeTab);
      }
    }
  }, [activeTab]);

  if (!activeTab) {
    return (
      <main id="tab-content" className="main-content">
        <div className="tab-placeholder">
          <h2>No surface open yet</h2>
          <p>Create or open a run, comparison, or candidates surface to get started.</p>
        </div>
      </main>
    );
  }

  return (
    <main id="tab-content" className="main-content">
      <TabsBar />
      {/* React surfaces */}
      {activeTab.kind === 'runs' && <RunsPane tab={activeTab} />}
      {activeTab.kind === 'compare' && <ComparePane tab={activeTab} />}
      {activeTab.kind === 'candidates' && <CandidatesPane tab={activeTab} />}
      {(activeTab.kind === 'run' || activeTab.kind === 'artifacts') && <RunDetailPane tab={activeTab} />}
      {activeTab.kind === 'paper' && <PaperOpsPane tab={activeTab} />}
      {activeTab.kind === 'system' && <SystemPane tab={activeTab} />}

      {/* Legacy surfaces - rendered via DOM container */}
      {!['runs', 'compare', 'candidates', 'run', 'artifacts', 'paper', 'system'].includes(activeTab.kind) && (
        <div
          ref={legacyContainerRef}
          className="legacy-surface-container"
          data-tab-id={activeTab.id}
          data-tab-kind={activeTab.kind}
        >
          {/* Legacy content will be mounted here by app-legacy.js */}
        </div>
      )}
    </main>
  );
}
