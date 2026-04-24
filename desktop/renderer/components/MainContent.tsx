import React from 'react';
import type { Tab } from '../../shared/models/tab';
import { assertNever } from '../../shared/assertNever';
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
import { LaunchPane } from './LaunchPane';

/**
 * MainContent — routes the active tab to its React surface.
 *
 * The switch in renderSurface() is exhaustive over the Tab discriminated union.
 * Adding a new TabKind to shared/models/tab.ts without adding a case here
 * produces a compile-time error at the assertNever(tab) call (#454).
 */
export default function MainContent({
  activeTab,
  allTabs,
  onTabChange,
}: {
  activeTab: Tab | null;
  allTabs?: Tab[];
  onTabChange?: (tabId: string) => void;
}) {
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
      {renderSurface(activeTab)}
    </main>
  );
}

/**
 * Exhaustive switch over Tab.kind.
 * TypeScript enforces that every TabKind has a case here.
 * Any unhandled kind is a compile error — not a silent blank tab.
 */
function renderSurface(tab: Tab): React.ReactElement {
  switch (tab.kind) {
    case 'runs':
      return <RunsPane tab={tab as any} />;
    case 'run':
      return <RunDetailPane tab={tab as any} />;
    case 'artifacts':
      return <RunDetailPane tab={tab as any} />;
    case 'compare':
      return <ComparePane tab={tab as any} />;
    case 'candidates':
      return <CandidatesPane tab={tab as any} />;
    case 'system':
      return <SystemPane tab={tab as any} />;
    case 'experiments':
      return <ExperimentsPane tab={tab as any} />;
    case 'paper':
      return <PaperOpsPane tab={tab as any} />;
    case 'job':
      return <JobLaunchReviewPane tab={tab as any} />;
    case 'assistant':
      return <AssistantPane tab={tab as any} />;
    case 'launch':
      return <LaunchPane tab={tab} />;
    case 'hypothesis':
      return (
        <StubSurfacePane
          tab={tab}
          issueRef="#266"
          description="Hypothesis Builder is planned. Implementation tracked in #266."
        />
      );
    default:
      // assertNever produces a compile error if any TabKind is unhandled above.
      return assertNever(tab);
  }
}

function StubSurfacePane({
  tab,
  issueRef,
  description,
}: {
  tab: { kind: string; title?: string };
  issueRef: string;
  description: string;
}) {
  return (
    <div className="tab-shell tab-placeholder" data-tab-kind={tab.kind}>
      <div className="section-label">Coming soon — {issueRef}</div>
      <h2>{tab.title || tab.kind}</h2>
      <p>{description}</p>
    </div>
  );
}
