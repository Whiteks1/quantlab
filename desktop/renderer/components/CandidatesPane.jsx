import React, { useMemo } from 'react';
import { useQuantLab } from './QuantLabContext';
import {
  formatCount,
  formatPercent,
  formatNumber,
  titleCase,
  toneClass,
} from '../modules/utils';
import './CandidatesPane.css';

const FILTER_OPTIONS = ['all', 'shortlist', 'baseline'];

/**
 * CandidatesPane — Candidates and shortlist decision layer.
 * Mirrors renderCandidatesTab() from app-legacy.js.
 */
export function CandidatesPane({ tab }) {
  const {
    state,
    getRuns,
    decision,
    toggleCandidate,
    setBaseline,
    toggleShortlist,
  } = useQuantLab();

  const filter = tab.filter || 'all';

  // Get all candidates sorted by baseline, shortlist, recency
  const allEntries = decision.getCandidateEntriesResolved();
  const sortedEntries = useMemo(() => {
    return [...allEntries].sort((left, right) => {
      const leftBaseline = decision.isBaselineRun(left.run_id) ? 1 : 0;
      const rightBaseline = decision.isBaselineRun(right.run_id) ? 1 : 0;
      if (leftBaseline !== rightBaseline) return rightBaseline - leftBaseline;

      const leftShortlist = left.shortlisted ? 1 : 0;
      const rightShortlist = right.shortlisted ? 1 : 0;
      if (leftShortlist !== rightShortlist)
        return rightShortlist - leftShortlist;

      const leftCreated = new Date(left.run?.created_at || 0).getTime();
      const rightCreated = new Date(right.run?.created_at || 0).getTime();
      return rightCreated - leftCreated;
    });
  }, [allEntries, decision]);

  // Apply filter
  const shortlistEntries = sortedEntries.filter((e) => e.shortlisted);
  let visibleEntries = sortedEntries;
  if (filter === 'shortlist') {
    visibleEntries = shortlistEntries;
  } else if (filter === 'baseline') {
    visibleEntries = sortedEntries.filter(
      (e) => e.run_id === state.candidatesStore.baseline_run_id
    );
  }

  const compareReady =
    shortlistEntries.length + (state.candidatesStore.baseline_run_id ? 1 : 0) >= 2;

  return (
    <div className="tab-shell candidates-tab">
      {/* Header */}
      <div className="artifact-top">
        <div>
          <div className="section-label">Decision layer</div>
          <h3>Candidates and shortlist</h3>
          <div className="artifact-meta">
            Persisted locally in QuantLab Desktop. This is the minimum layer
            that turns observation into choice.
          </div>
        </div>
        <div className="artifact-actions">
          <button className="ghost-btn">Open shortlist compare</button>
          {state.candidatesStore.baseline_run_id && (
            <button className="ghost-btn">Open baseline</button>
          )}
        </div>
      </div>

      {/* Summary cards */}
      <div className="tab-summary-grid">
        <SummaryCard label="Candidates" value={String(sortedEntries.length)} />
        <SummaryCard label="Shortlisted" value={String(shortlistEntries.length)} />
        <SummaryCard
          label="Baseline"
          value={state.candidatesStore.baseline_run_id || 'None'}
        />
        <SummaryCard
          label="Indexed runs"
          value={String(getRuns().length)}
        />
      </div>

      {/* Candidates workbench: list + sidebar */}
      <div className="candidates-workbench">
        <div className="candidates-workbench-main">
          <div className="artifact-panel">
            <div className="section-label">{titleCase(filter)}</div>
            <h3>Decision queue</h3>
            <div className="artifact-meta">
              Sorted by baseline, shortlist, and recency so the queue behaves
              like a real operator surface.
            </div>
            {visibleEntries.length ? (
              <div className="candidate-list">
                {visibleEntries.map((entry) => (
                  <CandidateCard
                    key={entry.run_id}
                    entry={entry}
                    isBaseline={
                      entry.run_id === state.candidatesStore.baseline_run_id
                    }
                  />
                ))}
              </div>
            ) : (
              <div className="empty-state">
                No runs match this candidate filter yet.
              </div>
            )}
          </div>
        </div>

        <aside className="candidates-workbench-side">
          <div className="artifact-panel">
            <div className="section-label">Queue controls</div>
            <h3>Focus the decision queue</h3>
            <div className="workflow-actions compare-rank-actions">
              {FILTER_OPTIONS.map((option) => (
                <button
                  key={option}
                  className={`ghost-btn ${filter === option ? 'is-selected' : ''}`}
                  onClick={() => {
                    // This would trigger upsertTab in the parent
                  }}
                >
                  {titleCase(option)}
                </button>
              ))}
            </div>

            <dl className="metric-list">
              <dt>Visible entries</dt>
              <dd>{formatCount(visibleEntries.length)}</dd>
              <dt>Total candidates</dt>
              <dd>{formatCount(sortedEntries.length)}</dd>
              <dt>Shortlist ready</dt>
              <dd>{compareReady ? 'Yes' : 'No'}</dd>
            </dl>
          </div>
        </aside>
      </div>
    </div>
  );
}

/**
 * Summary card component
 */
function SummaryCard({ label, value }) {
  return (
    <article className="summary-card">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </article>
  );
}

/**
 * Individual candidate card
 */
function CandidateCard({ entry, isBaseline }) {
  const {
    decision,
    toggleCandidate,
    toggleShortlist,
    setBaseline,
    openTab,
  } = useQuantLab();

  const run = entry.run;
  if (!run) {
    return (
      <article className="candidate-card empty">
        <div className="candidate-id">{entry.run_id}</div>
        <div className="candidate-meta">Run not yet indexed</div>
      </article>
    );
  }

  return (
    <article className={`candidate-card ${isBaseline ? 'is-baseline' : ''}`}>
      <div className="candidate-top">
        <div className="candidate-info">
          <div className="candidate-id">{run.run_id}</div>
          <div className="candidate-meta">
            {titleCase(run.mode || 'unknown')} · {run.ticker || '-'} ·{' '}
            {run.created_at || 'unknown'}
          </div>
        </div>
        {isBaseline && <span className="badge baseline">Baseline</span>}
        {entry.shortlisted && (
          <span className="badge shortlist">Shortlisted</span>
        )}
      </div>

      <div className="candidate-metrics">
        <MetricChip
          label="Return"
          value={formatPercent(run.total_return)}
          tone={toneClass(run.total_return, true)}
        />
        <MetricChip
          label="Sharpe"
          value={formatNumber(run.sharpe_simple)}
        />
        <MetricChip
          label="Drawdown"
          value={formatPercent(run.max_drawdown)}
          tone={toneClass(run.max_drawdown, false)}
        />
        <MetricChip label="Trades" value={formatCount(run.trades)} />
      </div>

      <div className="candidate-actions">
        <button
          className="ghost-btn mini"
          onClick={() => openTab('run', run.run_id)}
        >
          Open run
        </button>
        <button
          className="ghost-btn mini"
          onClick={() => toggleCandidate(run.run_id)}
        >
          {decision.isCandidateRun(run.run_id) ? 'Unmark' : 'Mark'} candidate
        </button>
        <button
          className="ghost-btn mini"
          onClick={() => toggleShortlist(run.run_id)}
        >
          {entry.shortlisted ? 'Remove from' : 'Add to'} shortlist
        </button>
        <button
          className="ghost-btn mini"
          onClick={() => setBaseline(run.run_id)}
        >
          {isBaseline ? 'Unset' : 'Set'} baseline
        </button>
      </div>
    </article>
  );
}

/**
 * Metric chip component
 */
function MetricChip({ label, value, tone = '' }) {
  return (
    <span className={`metric-chip ${tone || ''}`}>
      {label} {value}
    </span>
  );
}
