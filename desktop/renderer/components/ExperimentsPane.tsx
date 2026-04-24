import React, { useState, useMemo } from 'react';
import type { ExperimentsTab } from '../../shared/models/tab';
import {
  formatDateTime,
  formatBytes,
  formatPercent,
  formatNumber,
  formatCount,
  titleCase,
  toneClass,
} from '../modules/utils';
import { useQuantLab as _useQuantLab } from './QuantLabContext';

// QuantLabContext is a JS file; cast to any so strict-mode TSX can consume it.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const useQuantLab = _useQuantLab as () => any;

// ── Sub-components ────────────────────────────────────────────────────────────

function SummaryCard({ label, value, tone = '' }: { label: string; value: string; tone?: string }) {
  return (
    <article className={`summary-card ${tone}`}>
      <div className="label">{label}</div>
      <div className={`value ${tone}`}>{value}</div>
    </article>
  );
}

function ConfigCard({
  config,
  isSelected,
  onSelect,
  onLaunch,
  onOpen,
}: {
  config: any;
  isSelected: boolean;
  onSelect: () => void;
  onLaunch: () => void;
  onOpen: () => void;
}) {
  return (
    <article className={`candidate-card ${isSelected ? 'is-selected' : ''}`}>
      <div className="run-row-top">
        <div className="run-row-title">
          <strong>{config.name}</strong>
          <div className="run-row-meta">
            <span>{config.relativePath}</span>
            <span>{formatDateTime(config.modifiedAt)}</span>
            <span>{formatBytes(config.sizeBytes)}</span>
          </div>
        </div>
      </div>
      <div className="workflow-actions">
        <button className="ghost-btn" type="button" onClick={onSelect}>
          {isSelected ? 'Selected' : 'Preview'}
        </button>
        <button className="ghost-btn" type="button" onClick={onLaunch}>
          Launch sweep
        </button>
        <button className="ghost-btn" type="button" onClick={onOpen}>
          Open file
        </button>
      </div>
    </article>
  );
}

function SweepCard({
  sweep,
  isSelected,
  onSelect,
  onRelaunch,
  onOpenFolder,
}: {
  sweep: any;
  isSelected: boolean;
  onSelect: () => void;
  onRelaunch: () => void;
  onOpenFolder: () => void;
}) {
  return (
    <article className={`candidate-card ${isSelected ? 'is-selected' : ''}`}>
      <div className="run-row-top">
        <div className="run-row-title">
          <strong>{sweep.run_id}</strong>
          <div className="run-row-meta">
            <span>{titleCase(sweep.mode || 'unknown')}</span>
            <span>{sweep.configName || sweep.configPath || '-'}</span>
            <span>{formatDateTime(sweep.createdAt)}</span>
          </div>
        </div>
        <span className="mode-chip">{titleCase(sweep.mode || 'sweep')}</span>
      </div>
      <div className="run-row-metrics">
        <span className={`metric-chip ${toneClass(sweep.headlineReturn, true)}`}>
          Return {formatPercent(sweep.headlineReturn)}
        </span>
        <span className="metric-chip">Sharpe {formatNumber(sweep.headlineSharpe)}</span>
        <span className={`metric-chip ${toneClass(sweep.headlineDrawdown, false)}`}>
          Drawdown {formatPercent(sweep.headlineDrawdown)}
        </span>
        <span className="metric-chip">Runs {formatCount(sweep.nRuns)}</span>
      </div>
      <div className="workflow-actions">
        <button className="ghost-btn" type="button" onClick={onSelect}>
          {isSelected ? 'Selected' : 'Open details'}
        </button>
        {sweep.configPath && (
          <button className="ghost-btn" type="button" onClick={onRelaunch}>
            Launch again
          </button>
        )}
        <button className="ghost-btn" type="button" onClick={onOpenFolder}>
          Folder
        </button>
      </div>
    </article>
  );
}

function DecisionFlags({ store, sweepDecision, entryId }: { store: any; sweepDecision: any; entryId: string }) {
  const isBaseline = sweepDecision.isBaseline(store, entryId);
  const isShortlisted = sweepDecision.isShortlisted(store, entryId);
  const isTracked = sweepDecision.isTracked(store, entryId);
  if (!isBaseline && !isShortlisted && !isTracked) {
    return <span className="candidate-flag neutral">Untracked</span>;
  }
  return (
    <>
      {isBaseline && <span className="candidate-flag baseline">Baseline</span>}
      {isShortlisted && <span className="candidate-flag shortlist">Shortlist</span>}
      {isTracked && <span className="candidate-flag candidate">Tracked</span>}
    </>
  );
}

function SweepDecisionCard({
  entry,
  store,
  sweepDecision,
  onToggle,
  onToggleShortlist,
  onSetBaseline,
}: {
  entry: any;
  store: any;
  sweepDecision: any;
  onToggle: (row: any) => void;
  onToggleShortlist: (entryId: string) => void;
  onSetBaseline: (entryId: string) => void;
}) {
  const row = entry.row || entry.row_snapshot || entry;
  const isTracked = sweepDecision.isTracked(store, entry.entry_id);
  return (
    <article className="candidate-card">
      <div className="run-row-top">
        <div className="run-row-title">
          <strong>{entry.entry_id}</strong>
          <div className="run-row-meta">
            <span>Sweep {entry.sweep_run_id || '-'}</span>
            {entry.config_path && <span>{entry.config_path}</span>}
          </div>
        </div>
        <div className="candidate-flags">
          <DecisionFlags store={store} sweepDecision={sweepDecision} entryId={entry.entry_id} />
        </div>
      </div>
      {row && (
        <div className="run-row-metrics">
          <span className={`metric-chip ${toneClass(Number(row.total_return), true)}`}>
            Return {formatPercent(Number(row.total_return))}
          </span>
          <span className="metric-chip">
            Sharpe {formatNumber(Number(row.sharpe_simple ?? row.best_test_sharpe))}
          </span>
          <span className={`metric-chip ${toneClass(Number(row.max_drawdown), false)}`}>
            Drawdown {formatPercent(Number(row.max_drawdown))}
          </span>
        </div>
      )}
      <div className="workflow-actions">
        <button className="ghost-btn" type="button" onClick={() => onToggle(entry)}>
          {isTracked ? 'Untrack' : 'Track'}
        </button>
        {isTracked && (
          <>
            <button className="ghost-btn" type="button" onClick={() => onToggleShortlist(entry.entry_id)}>
              {sweepDecision.isShortlisted(store, entry.entry_id) ? 'Remove from shortlist' : 'Shortlist'}
            </button>
            <button className="ghost-btn" type="button" onClick={() => onSetBaseline(entry.entry_id)}>
              {sweepDecision.isBaseline(store, entry.entry_id) ? 'Clear baseline' : 'Set baseline'}
            </button>
          </>
        )}
      </div>
    </article>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function ExperimentsPane({ tab }: { tab: ExperimentsTab }) {
  const ctx = useQuantLab();
  const { state, refresh, toggleSweepEntry, toggleSweepShortlist, setSweepBaseline, findSweepDecisionRow } = ctx;

  const workspace = state.experimentsWorkspace ?? { status: 'idle', configs: [], sweeps: [], error: null };
  const configs: any[] = Array.isArray(workspace.configs) ? workspace.configs : [];
  const sweeps: any[] = Array.isArray(workspace.sweeps) ? workspace.sweeps : [];
  const sweepDecisionStore = state.sweepDecisionStore ?? {};
  const sweepDecision = state.sweepDecision ?? {};

  const [selectedConfigPath, setSelectedConfigPath] = useState<string | null>(
    tab.selectedConfigPath ?? configs[0]?.path ?? null
  );
  const [selectedSweepId, setSelectedSweepId] = useState<string | null>(
    tab.selectedSweepId ?? sweeps[0]?.run_id ?? null
  );

  const selectedConfig = configs.find((c) => c.path === selectedConfigPath) ?? configs[0] ?? null;
  const selectedSweep = sweeps.find((s) => s.run_id === selectedSweepId) ?? sweeps[0] ?? null;
  const latestSweep = sweeps[0] ?? null;

  const sweepDecisionEntries = useMemo(() => {
    if (typeof sweepDecision.getEntriesResolved !== 'function') return [];
    return sweepDecision.getEntriesResolved(sweepDecisionStore, findSweepDecisionRow);
  }, [sweepDecision, sweepDecisionStore, findSweepDecisionRow]);

  const sweepShortlistEntries = sweepDecisionEntries.filter((e: any) => e.shortlisted);
  const sweepBaselineEntryId = sweepDecisionStore?.baseline_entry_id ?? null;

  const selectedSweepFiles: any[] = selectedSweep?.files ?? [];
  const fileByName = (name: string) => selectedSweepFiles.find((f) => f.name === name) ?? null;
  const selectedSweepResultRows: any[] = selectedSweep?.topResults?.length
    ? selectedSweep.topResults
    : selectedSweep?.leaderboardRows ?? [];

  const openPath = (p: string) => {
    if (typeof window.quantlabDesktop?.openPath === 'function') {
      window.quantlabDesktop.openPath(p);
    }
  };

  const handleLaunchSweep = async (configPath: string) => {
    if (!configPath) return;
    try {
      await window.quantlabDesktop.postJson('/api/launch-control', {
        command: 'sweep',
        params: { config_path: configPath },
      });
      await refresh();
    } catch (err) {
      console.error('ExperimentsPane: launch sweep failed', err);
    }
  };

  if (workspace.status === 'loading' && !configs.length && !sweeps.length) {
    return (
      <div className="tab-placeholder">
        Reading experiment configs and recent sweep artifacts from the local workspace...
      </div>
    );
  }

  if (workspace.status === 'error' && !configs.length && !sweeps.length) {
    return (
      <div className="tab-placeholder">
        {workspace.error || 'Could not read local experiment workspace.'}
      </div>
    );
  }

  return (
    <div className="tab-shell experiments-pane" data-smoke="surface-experiments">
      {/* Header */}
      <div className="artifact-top">
        <div>
          <div className="section-label">Experiment workspace</div>
          <h3>Configs and recent sweeps</h3>
          <div className="artifact-meta">
            Local-first shell surface for launching sweeps, inspecting their outputs, and resuming
            quantitative iteration without leaving QuantLab Desktop.
          </div>
        </div>
        <div className="workflow-actions">
          <button className="ghost-btn" type="button" onClick={() => refresh()}>
            Refresh
          </button>
          {selectedConfig && (
            <button
              className="ghost-btn"
              type="button"
              onClick={() => handleLaunchSweep(selectedConfig.path)}
            >
              Launch selected config
            </button>
          )}
          {selectedSweep && (
            <button className="ghost-btn" type="button" onClick={() => openPath(selectedSweep.path)}>
              Open sweep folder
            </button>
          )}
        </div>
      </div>

      {/* Summary cards */}
      <div className="tab-summary-grid">
        <SummaryCard label="Configs" value={String(configs.length)} />
        <SummaryCard label="Recent sweeps" value={String(sweeps.length)} />
        <SummaryCard label="Latest mode" value={latestSweep ? titleCase(latestSweep.mode || 'unknown') : 'None'} />
        <SummaryCard label="Latest sweep" value={latestSweep?.run_id || 'None'} />
        <SummaryCard label="Tracked sweep rows" value={String(sweepDecisionEntries.length)} />
        <SummaryCard label="Sweep shortlist" value={String(sweepShortlistEntries.length)} />
      </div>

      {/* Configs + preview */}
      <div className="artifact-grid experiments-grid">
        <section className="artifact-panel">
          <div className="section-label">Catalog</div>
          <h3>Experiment configs</h3>
          {configs.length ? (
            <div className="candidate-list">
              {configs.map((config) => (
                <ConfigCard
                  key={config.path}
                  config={config}
                  isSelected={selectedConfig?.path === config.path}
                  onSelect={() => setSelectedConfigPath(config.path)}
                  onLaunch={() => handleLaunchSweep(config.path)}
                  onOpen={() => openPath(config.path)}
                />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              No experiment configs were found under configs/experiments.
            </div>
          )}
        </section>

        <section className="artifact-panel">
          <div className="section-label">Preview</div>
          <h3>{selectedConfig?.name || 'Select a config'}</h3>
          {selectedConfig?.previewText ? (
            <pre className="log-preview config-preview">{selectedConfig.previewText}</pre>
          ) : (
            <div className="empty-state">
              Choose an experiment config to preview its YAML and launch a sweep from the shell.
            </div>
          )}
        </section>
      </div>

      {/* Sweeps + detail */}
      <div className="artifact-grid experiments-grid">
        <section className="artifact-panel">
          <div className="section-label">Recent outputs</div>
          <h3>Sweeps</h3>
          {sweeps.length ? (
            <div className="candidate-list">
              {sweeps.map((sweep) => (
                <SweepCard
                  key={sweep.run_id}
                  sweep={sweep}
                  isSelected={selectedSweep?.run_id === sweep.run_id}
                  onSelect={() => setSelectedSweepId(sweep.run_id)}
                  onRelaunch={() => handleLaunchSweep(sweep.configPath)}
                  onOpenFolder={() => openPath(sweep.path)}
                />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              No sweep output directories were found yet under outputs/sweeps.
            </div>
          )}
        </section>

        <section className="artifact-panel">
          <div className="section-label">Selected sweep</div>
          <h3>{selectedSweep?.run_id || 'Choose a sweep'}</h3>
          {selectedSweep ? (
            <>
              <div className="tab-summary-grid">
                <SummaryCard label="Mode" value={titleCase(selectedSweep.mode || 'unknown')} />
                <SummaryCard label="Config" value={selectedSweep.configName || 'Unknown'} />
                <SummaryCard label="Sweep runs" value={formatCount(selectedSweep.nRuns)} />
                <SummaryCard label="Selected test rows" value={formatCount(selectedSweep.nSelected)} />
                <SummaryCard label="Train runs" value={formatCount(selectedSweep.nTrainRuns)} />
                <SummaryCard label="Test runs" value={formatCount(selectedSweep.nTestRuns)} />
              </div>
              <div className="workflow-actions">
                <button className="ghost-btn" type="button" onClick={() => openPath(selectedSweep.path)}>
                  Open folder
                </button>
                {fileByName('meta.json') && (
                  <button className="ghost-btn" type="button" onClick={() => openPath(fileByName('meta.json').path)}>
                    meta.json
                  </button>
                )}
                {fileByName('leaderboard.csv') && (
                  <button className="ghost-btn" type="button" onClick={() => openPath(fileByName('leaderboard.csv').path)}>
                    leaderboard.csv
                  </button>
                )}
                {fileByName('experiments.csv') && (
                  <button className="ghost-btn" type="button" onClick={() => openPath(fileByName('experiments.csv').path)}>
                    experiments.csv
                  </button>
                )}
                {fileByName('config_resolved.yaml') && (
                  <button className="ghost-btn" type="button" onClick={() => openPath(fileByName('config_resolved.yaml').path)}>
                    config_resolved.yaml
                  </button>
                )}
              </div>
              <div className="artifact-grid">
                <section className="artifact-panel">
                  <div className="section-label">Top rows</div>
                  <h3>Leaderboard snapshot</h3>
                  {selectedSweepResultRows.length ? (
                    <div className="mini-table">
                      <div className="mini-table-row head">
                        <span>Return</span>
                        <span>Sharpe</span>
                        <span>Drawdown</span>
                        <span>Trades</span>
                      </div>
                      {selectedSweepResultRows.map((row: any, i: number) => (
                        <div key={i} className="mini-table-row">
                          <span className={toneClass(Number(row.total_return), true)}>
                            {formatPercent(Number(row.total_return))}
                          </span>
                          <span>{formatNumber(Number(row.sharpe_simple ?? row.best_test_sharpe))}</span>
                          <span className={toneClass(Number(row.max_drawdown), false)}>
                            {formatPercent(Number(row.max_drawdown))}
                          </span>
                          <span>{formatCount(Number(row.trades ?? row.n_test_runs))}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">No leaderboard rows were readable for this sweep.</div>
                  )}
                </section>
                <section className="artifact-panel">
                  <div className="section-label">Walkforward summary</div>
                  <h3>Selection and OOS</h3>
                  {selectedSweep.walkforwardRows?.length ? (
                    <div className="mini-table">
                      <div className="mini-table-row head">
                        <span>Split</span>
                        <span>Best test sharpe</span>
                        <span>Best test return</span>
                        <span>Selected</span>
                      </div>
                      {selectedSweep.walkforwardRows.map((row: any, i: number) => (
                        <div key={i} className="mini-table-row">
                          <span>{row.split_name || '-'}</span>
                          <span>{formatNumber(Number(row.best_test_sharpe))}</span>
                          <span>{formatPercent(Number(row.best_test_return))}</span>
                          <span>{formatCount(Number(row.n_selected))}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">This sweep did not expose walkforward summary rows.</div>
                  )}
                </section>
              </div>

              {/* Decision handoff for selected sweep */}
              <section className="artifact-panel">
                <div className="section-label">Decision handoff</div>
                <h3>Track top sweep rows</h3>
                <div className="tab-summary-grid">
                  <SummaryCard label="Tracked" value={String(sweepDecisionEntries.length)} />
                  <SummaryCard label="Shortlisted" value={String(sweepShortlistEntries.length)} />
                  <SummaryCard label="Baseline" value={sweepBaselineEntryId ?? 'None'} />
                </div>
                {selectedSweep.decisionRows?.length ? (
                  <div className="candidate-list">
                    {selectedSweep.decisionRows.map((row: any) => (
                      <SweepDecisionCard
                        key={row.entry_id}
                        entry={row}
                        store={sweepDecisionStore}
                        sweepDecision={sweepDecision}
                        onToggle={toggleSweepEntry}
                        onToggleShortlist={toggleSweepShortlist}
                        onSetBaseline={setSweepBaseline}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    This sweep did not expose comparable leaderboard rows for handoff.
                  </div>
                )}
              </section>

              {/* Workspace files */}
              <section className="artifact-panel">
                <div className="section-label">Workspace files</div>
                <h3>Local sweep directory</h3>
                {selectedSweepFiles.length ? (
                  <div className="system-link-list">
                    {selectedSweepFiles.slice(0, 12).map((f: any) => (
                      <button
                        key={f.path}
                        className="system-link-item"
                        type="button"
                        onClick={() => openPath(f.path)}
                      >
                        <strong>{f.name}</strong>
                        <span>{formatBytes(f.sizeBytes)}</span>
                      </button>
                    ))}
                    {selectedSweep.filesTruncated && (
                      <div className="artifact-meta">Directory listing truncated.</div>
                    )}
                  </div>
                ) : (
                  <div className="empty-state">No files are listed for this sweep directory.</div>
                )}
              </section>
            </>
          ) : (
            <div className="empty-state">Select a recent sweep to inspect its local outputs.</div>
          )}
        </section>
      </div>

      {/* Tracked handoff — all entries */}
      <section className="artifact-panel">
        <div className="section-label">Tracked handoff</div>
        <h3>Sweep shortlist and baseline</h3>
        {sweepDecisionEntries.length ? (
          <div className="candidate-list">
            {sweepDecisionEntries.map((entry: any) => (
              <SweepDecisionCard
                key={entry.entry_id}
                entry={entry}
                store={sweepDecisionStore}
                sweepDecision={sweepDecision}
                onToggle={toggleSweepEntry}
                onToggleShortlist={toggleSweepShortlist}
                onSetBaseline={setSweepBaseline}
              />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            No sweep rows are tracked yet. Track a top row from the selected sweep to start the
            handoff layer.
          </div>
        )}
      </section>
    </div>
  );
}
