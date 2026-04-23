import React from 'react';
import { RunsPane } from './RunsPane';
import { ComparePane } from './ComparePane';
import { CandidatesPane } from './CandidatesPane';
import { RunDetailPane } from './RunDetailPane';
import { TabsBar } from './TabsBar';
import { PaperOpsPane } from './PaperOpsPane';
import { SystemPane } from './SystemPane';
import { ExperimentsPane } from './ExperimentsPane';
import { JobLaunchReviewPane } from './JobLaunchReviewPane';
import { AssistantPane } from './AssistantPane';

/**
 * MainContent - Main content area that:
 * - Mounts React-based surfaces (Runs, Compare, Candidates)
 * - Shows explicit paused placeholders for surfaces not owned in this slice
 * - Manages surface tab context and active tab rendering
 * 
 * Surfaces are mounted based on activeTab.kind:
 * - 'runs': RunsPane
 * - 'compare': ComparePane
 * - 'candidates': CandidatesPane
 * - Other kinds: explicit React-owned pause state
 */
export default function MainContent({ activeTab, allTabs, onTabChange }) {
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
      {activeTab.kind === 'experiments' && <ExperimentsPane tab={activeTab} />}
      {activeTab.kind === 'job' && <JobLaunchReviewPane tab={activeTab} />}
      {activeTab.kind === 'assistant' && <AssistantPane tab={activeTab} />}

      {/* Stub surfaces — guarded placeholders pending full implementation */}
      {activeTab.kind === 'launch' && <StubSurfacePane tab={activeTab} issueRef="#412" description="Native Launch surface is a post-v1 milestone. Use the research_ui launch flow in the meantime." />}
      {activeTab.kind === 'hypothesis' && <StubSurfacePane tab={activeTab} issueRef="#266" description="Hypothesis Builder is planned. Implementation tracked in #266." />}

      {!['runs', 'compare', 'candidates', 'run', 'artifacts', 'paper', 'system', 'experiments', 'job', 'assistant', 'launch', 'hypothesis'].includes(activeTab.kind) && (
        <PausedSurfacePane tab={activeTab} />
      )}
    </main>
  );
}

function PausedSurfacePane({ tab }) {
  return (
    <div className="tab-shell tab-placeholder" data-tab-kind={tab.kind}>
      <div className="section-label">React runtime boundary</div>
      <h2>{tab.title || 'Surface paused'}</h2>
      <p>
        This surface is visible in the React-owned shell, but its product
        expansion remains out of scope for #430.
      </p>
    </div>
  );
}

function StubSurfacePane({ tab, issueRef, description }) {
  return (
    <div className="tab-shell tab-placeholder" data-tab-kind={tab.kind}>
      <div className="section-label">Coming soon — {issueRef}</div>
      <h2>{tab.title || tab.kind}</h2>
      <p>{description}</p>
    </div>
  );
}
