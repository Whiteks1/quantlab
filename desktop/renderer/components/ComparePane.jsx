import React, { useState, useEffect, useMemo } from 'react';
import { useQuantLab } from './QuantLabContext';
import {
  formatCount,
  formatPercent,
  formatNumber,
  rankRunsByMetric,
  collectConfigDeltas,
  titleCase,
  toneClass,
  formatMetricForDisplay,
} from '../modules/utils';
import './ComparePane.css';

const RANK_METRICS = [
  'sharpe_simple',
  'total_return',
  'max_drawdown',
  'trades',
];

/**
 * ComparePane — Decision-oriented multi-run comparison.
 * Mirrors renderCompareTab() from app-legacy.js.
 */
export function ComparePane({ tab }) {
  const { state, findRun, decision, loadRunDetail } = useQuantLab();
  const [detailMap, setDetailMap] = useState(tab.detailMap || {});
  const [loading, setLoading] = useState(tab.status === 'loading');

  // Load run details on mount if not already loaded
  useEffect(() => {
    if (loading && tab.runIds?.length) {
      (async () => {
        try {
          const details = await Promise.all(
            tab.runIds.map(async (runId) => {
              try {
                const detail = await loadRunDetail(runId);
                return [runId, detail];
              } catch (_err) {
                return [runId, null];
              }
            })
          );
          setDetailMap(Object.fromEntries(details));
          setLoading(false);
        } catch (_err) {
          setLoading(false);
        }
      })();
    }
  }, [tab.runIds, loading, loadRunDetail]);

  const runs = (tab.runIds || []).map(findRun).filter(Boolean);
  if (runs.length < 2) {
    return (
      <div className="tab-placeholder">
        The selected compare set is no longer available in the registry.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="tab-placeholder">
        Preparing decision-oriented compare for {runs.length} runs...
      </div>
    );
  }

  const rankMetric = tab.rankMetric || 'sharpe_simple';
  const rankedRuns = rankRunsByMetric(runs, rankMetric);
  const winner = rankedRuns[0];
  const runnerUp = rankedRuns[1] || null;
  const configDeltaEntries = collectConfigDeltas(runs, detailMap);

  const baselineInSet = runs.find((r) =>
    decision.isBaselineRun(r.run_id)
  ) || null;
  const shortlistedCount = runs.filter((r) =>
    decision.isShortlistedRun(r.run_id)
  ).length;

  return (
    <div className="compare-shell compare-tab">
      {/* Summary cards */}
      <div className="tab-summary-grid">
        <SummaryCard label="Compared runs" value={String(runs.length)} />
        <SummaryCard
          label="Ranking metric"
          value={titleCase(rankMetric.replace('_', ' '))}
        />
        <SummaryCard
          label="Winner"
          value={`${winner.run_id} · ${formatMetricForDisplay(
            winner[rankMetric],
            rankMetric
          )}`}
          tone={
            rankMetric === 'max_drawdown'
              ? toneClass(winner.max_drawdown, false)
              : toneClass(winner[rankMetric], true)
          }
        />
        <SummaryCard
          label="Runner-up"
          value={
            runnerUp
              ? `${runnerUp.run_id} · ${formatMetricForDisplay(
                  runnerUp[rankMetric],
                  rankMetric
                )}`
              : '-'
          }
        />
        <SummaryCard
          label="Baseline in set"
          value={baselineInSet ? baselineInSet.run_id : 'No'}
        />
        <SummaryCard
          label="Shortlisted in set"
          value={String(shortlistedCount)}
        />
      </div>

      {/* Compare workbench: table + sidebar */}
      <div className="compare-workbench">
        <div className="compare-workbench-main">
          <div className="artifact-panel">
            <div className="section-label">Ranking matrix</div>
            <h3>Decision-ready compare set</h3>
            <div className="artifact-meta">
              Rank, inspect, and promote runs without leaving the compare
              surface.
            </div>
            <CompareRankingTable
              rankedRuns={rankedRuns}
              rankMetric={rankMetric}
            />
          </div>

          <div className="artifact-panel">
            <div className="section-label">Config deltas</div>
            <h3>What changes across this compare set</h3>
            {configDeltaEntries.length ? (
              <div className="mini-table">
                <div className="mini-table-row head">
                  <span>Key</span>
                  <span>Values</span>
                </div>
                {configDeltaEntries.map(([key, values]) => (
                  <div key={key} className="mini-table-row">
                    <span>{key}</span>
                    <span>{values.join(' | ')}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                No resolved config deltas for this compare set.
              </div>
            )}
          </div>
        </div>

        <aside className="compare-workbench-side">
          <div className="artifact-panel run-spotlight-card compare-winner-card">
            <div className="section-label">Current leader</div>
            <h3>{winner.run_id}</h3>
            <div className="artifact-meta">
              {titleCase(winner.mode || 'unknown')} · ranked by{' '}
              {titleCase(rankMetric.replace('_', ' '))}
            </div>
            <dl className="metric-list compact">
              <dt>Rank metric</dt>
              <dd
                className={
                  rankMetric === 'max_drawdown'
                    ? toneClass(winner.max_drawdown, false)
                    : toneClass(winner[rankMetric], true)
                }
              >
                {formatMetricForDisplay(winner[rankMetric], rankMetric)}
              </dd>
              <dt>Return</dt>
              <dd className={toneClass(winner.total_return, true)}>
                {formatPercent(winner.total_return)}
              </dd>
              <dt>Sharpe</dt>
              <dd>{formatNumber(winner.sharpe_simple)}</dd>
              <dt>Drawdown</dt>
              <dd className={toneClass(winner.max_drawdown, false)}>
                {formatPercent(winner.max_drawdown)}
              </dd>
              <dt>Trades</dt>
              <dd>{formatCount(winner.trades)}</dd>
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
function SummaryCard({ label, value, tone = '' }) {
  return (
    <article className={`summary-card ${tone || ''}`}>
      <div className="label">{label}</div>
      <div className={`value ${tone || ''}`}>{value}</div>
    </article>
  );
}

/**
 * Ranking table showing all runs ranked by selected metric
 */
function CompareRankingTable({ rankedRuns, rankMetric }) {
  const { decision, toggleCandidate, setBaseline, toggleShortlist } = useQuantLab();
  const [selectedMetric, setSelectedMetric] = useState(rankMetric);

  return (
    <div className="compare-ranking-table">
      <div className="metric-selector">
        <label htmlFor="rank-metric">Rank by:</label>
        <select
          id="rank-metric"
          value={selectedMetric}
          onChange={(e) => setSelectedMetric(e.target.value)}
        >
          {RANK_METRICS.map((metric) => (
            <option key={metric} value={metric}>
              {titleCase(metric.replace('_', ' '))}
            </option>
          ))}
        </select>
      </div>

      <table className="runs-compare-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Run ID</th>
            <th className="metric-col">{titleCase(selectedMetric.replace('_', ' '))}</th>
            <th>Return</th>
            <th>Sharpe</th>
            <th>Drawdown</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {rankedRuns.map((run, idx) => (
            <tr key={run.run_id}>
              <td className="rank">{idx + 1}</td>
              <td className="run-id">{run.run_id}</td>
              <td
                className={`metric-col ${
                  selectedMetric === 'max_drawdown'
                    ? toneClass(run.max_drawdown, false)
                    : toneClass(run[selectedMetric], true)
                }`}
              >
                {formatMetricForDisplay(run[selectedMetric], selectedMetric)}
              </td>
              <td className={toneClass(run.total_return, true)}>
                {formatPercent(run.total_return)}
              </td>
              <td>{formatNumber(run.sharpe_simple)}</td>
              <td className={toneClass(run.max_drawdown, false)}>
                {formatPercent(run.max_drawdown)}
              </td>
              <td className="actions">
                <button
                  className="ghost-btn mini"
                  onClick={() => toggleCandidate(run.run_id)}
                >
                  {decision.isCandidateRun(run.run_id) ? 'Unmark' : 'Mark'} candidate
                </button>
                <button
                  className="ghost-btn mini"
                  onClick={() => setBaseline(run.run_id)}
                >
                  Set baseline
                </button>
                <button
                  className="ghost-btn mini"
                  onClick={() => toggleShortlist(run.run_id)}
                >
                  {decision.isShortlistedRun(run.run_id) ? 'Remove' : 'Add'} to shortlist
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
