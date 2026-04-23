import React, { useMemo } from 'react';
import { useQuantLab } from './QuantLabContext';
import {
  formatCount,
  formatPercent,
  formatNumber,
  formatDateTime,
  formatBytes,
  titleCase,
  toneClass,
  shortCommit,
  selectPrimaryResult,
  selectTopResults,
  summarizeObjectEntries,
  buildRunArtifactHref,
} from '../modules/utils';
import './RunDetailPane.css';

// Local UI helpers
function resolveDecisionSignal(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("baseline")) return { label: "Pinned baseline", tone: "tone-positive" };
  if (normalized.includes("shortlist")) return { label: "Shortlisted", tone: "tone-positive" };
  if (normalized.includes("candidate")) return { label: "Candidate review", tone: "tone-warning" };
  return { label: "Untracked", tone: "tone-neutral" };
}

function resolveLaunchSignal(value, options = {}) {
  const normalized = String(value || "").toLowerCase();
  const emptyLabel = options.emptyLabel || "Launch pending";
  if (!normalized || normalized === "none" || normalized.includes("no linked")) {
    return { label: emptyLabel, tone: "tone-warning" };
  }
  if (normalized.includes("succeeded")) return { label: "Completed", tone: "tone-positive" };
  if (normalized.includes("failed")) return { label: "Failed", tone: "tone-negative" };
  if (normalized.includes("running") || normalized.includes("queued") || normalized.includes("pending")) {
    return { label: "In flight", tone: "tone-warning" };
  }
  if (normalized.includes("unknown")) return { label: "Review state", tone: "tone-warning" };
  return { label: titleCase(String(value)), tone: "tone-warning" };
}

export function RunDetailPane({ tab }) {
  const {
    state,
    findRun,
    decision,
    getRunRelatedJobs,
    getSweepDecisionEntriesForRun,
    toggleCandidate,
    setBaseline,
    toggleShortlist,
    openTab,
  } = useQuantLab();

  const run = findRun(tab.runId);

  if (!run) {
    return <div className="tab-shell run-detail-shell tab-placeholder">The requested run is no longer present in the registry.</div>;
  }
  if (tab.status === "loading") {
    return <div className="tab-shell run-detail-shell tab-placeholder">Reading canonical detail for {run.run_id}...</div>;
  }
  if (tab.status === "error") {
    return <div className="tab-shell run-detail-shell tab-placeholder">{tab.error || "Could not load run detail."}</div>;
  }

  const detail = tab.detail || {};
  const report = detail.report;
  const primaryResult = selectPrimaryResult(run, report);
  const configEntries = summarizeObjectEntries(report?.config_resolved);
  const fileEntries = Array.isArray(detail.directoryEntries) ? detail.directoryEntries : [];
  const artifacts = Array.isArray(report?.artifacts) ? report.artifacts : [];
  const topResults = selectTopResults(report?.results, 4);

  const candidateEntry = decision.getCandidateEntry(state.candidatesStore, run.run_id);
  const relatedJobs = getRunRelatedJobs(run.run_id);
  const latestRelatedJob = relatedJobs[0] || null;
  const sweepEntries = getSweepDecisionEntriesForRun(run.run_id);
  const decisionState = decision.summarizeCandidateState(state.candidatesStore, run.run_id);
  
  const hasDecisionPeers = decision.isBaselineRun(run.run_id)
    ? decision.getCandidateEntriesResolved().length > 1
    : Boolean(state.candidatesStore?.baseline_run_id || decision.isShortlistedRun(run.run_id));
  
  const decisionNote = candidateEntry?.note || "No local decision note yet.";
  
  const relatedJobSignal = resolveLaunchSignal(latestRelatedJob?.status, { emptyLabel: "Launch pending" });
  const continuityState = latestRelatedJob
    ? `${relatedJobSignal.label} · ${formatDateTime(latestRelatedJob.created_at)}`
    : relatedJobSignal.label;
    
  const isCandidate = decision.isCandidateRun(run.run_id);
  const isShortlist = decision.isShortlistedRun(run.run_id);
  const isBaseline = decision.isBaselineRun(run.run_id);

  return (
    <div className="tab-shell run-detail-shell">
      {/* Identity Header */}
      <div className="run-identity-header">
        <div className="run-identity-copy">
          <div className="section-label">Run workspace</div>
          <h2 className="run-identity-title">{run.run_id}</h2>
          <div className="run-identity-meta">
            <span>{run.ticker || "-"}</span>
            <span>{titleCase(run.mode || "unknown")}</span>
            <span>{formatDateTime(run.created_at)}</span>
            <span className="mono-cell">{shortCommit(run.git_commit) || "-"}</span>
          </div>
          <div className="run-identity-state">
            <span className={`badge ${resolveDecisionSignal(decisionState).tone}`}>{resolveDecisionSignal(decisionState).label}</span>
            <span className={`badge ${relatedJobSignal.tone}`}>{continuityState}</span>
          </div>
        </div>
        <div className="run-identity-side">
          <div className="workflow-actions">
            <button className="ghost-btn" onClick={() => toggleCandidate(run.run_id)}>
              {isCandidate ? 'Unmark' : 'Mark'} candidate
            </button>
            <button className="ghost-btn" onClick={() => toggleShortlist(run.run_id)}>
              {isShortlist ? 'Remove from shortlist' : 'Add to shortlist'}
            </button>
            <button className="ghost-btn" onClick={() => setBaseline(isBaseline ? null : run.run_id)}>
              {isBaseline ? 'Clear baseline' : 'Set as baseline'}
            </button>
            {detail.reportUrl && (
              <button className="ghost-btn" onClick={() => {
                // eslint-disable-next-line no-undef
                if (typeof window.quantlabDesktop?.openExternal === 'function') {
                  // eslint-disable-next-line no-undef
                  window.quantlabDesktop.openExternal(detail.reportUrl);
                }
              }}>
                Raw report
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Summary Section (Performance vs Evidence) */}
      <div className="tab-summary-grid">
        {tab.subview === "artifacts" ? (
          <>
            <SummaryCard 
              label="Workspace path" 
              value={run.path ? "Discoverable" : "Unavailable"} 
              tone={run.path ? "tone-positive" : "tone-warning"} 
            />
            <SummaryCard 
              label="Report.json" 
              value={detail.reportUrl ? "Available" : "Missing"} 
              tone={detail.reportUrl ? "tone-positive" : "tone-warning"} 
            />
            <SummaryCard 
              label="Manifest files" 
              value={artifacts.length ? formatCount(artifacts.length) : "None"} 
              tone={artifacts.length ? "tone-positive" : "tone-neutral"} 
            />
            <SummaryCard 
              label="Local files" 
              value={fileEntries.length ? formatCount(fileEntries.length) : "None"} 
              tone={fileEntries.length ? "tone-positive" : "tone-neutral"} 
            />
          </>
        ) : (
          <>
            <SummaryCard label="Return" value={formatPercent(run.total_return)} tone={toneClass(run.total_return, true)} />
            <SummaryCard label="Sharpe" value={formatNumber(run.sharpe_simple)} />
            <SummaryCard label="Drawdown" value={formatPercent(run.max_drawdown)} tone={toneClass(run.max_drawdown, false)} />
            <SummaryCard label="Trades" value={formatCount(run.trades)} />
          </>
        )}
      </div>

      {/* Main Grid: Overview & Artifacts combined */}
      <div className="run-detail-grid">
        <div className="run-detail-main stack">
          
          <section className="artifact-panel">
            <div className="section-label">Result evidence</div>
            <h3>Decision metric snapshot</h3>
            <div className="run-evidence-stack">
              <div className="run-evidence-block">
                {primaryResult ? (
                  <dl className="metric-list">
                    <dt>Return</dt><dd className={toneClass(primaryResult.total_return, true)}>{formatPercent(primaryResult.total_return)}</dd>
                    <dt>Sharpe</dt><dd>{formatNumber(primaryResult.sharpe_simple)}</dd>
                    <dt>Drawdown</dt><dd className={toneClass(primaryResult.max_drawdown, false)}>{formatPercent(primaryResult.max_drawdown)}</dd>
                    <dt>Trades</dt><dd>{formatCount(primaryResult.trades)}</dd>
                  </dl>
                ) : (
                  <div className="empty-state">No primary result available.</div>
                )}
              </div>
            </div>
          </section>

          <section className="artifact-panel">
            <div className="section-label">Config and provenance</div>
            <h3>How this run was produced</h3>
            <div className="run-evidence-stack">
              <div className="run-evidence-block">
                <dl className="metric-list">
                  <dt>Strategy</dt><dd className="mono-cell">{report?.config_received?.strategy?.strategy_name || "-"}</dd>
                  <dt>Data scope</dt><dd className="mono-cell">{report?.config_received?.data?.tickers?.join(", ") || "-"}</dd>
                  <dt>Horizon</dt><dd>{report?.config_received?.data?.start_date || "-"} to {report?.config_received?.data?.end_date || "-"}</dd>
                  <dt>Execution</dt><dd>{report?.config_received?.execution?.broker || "paper"}</dd>
                </dl>
              </div>
              <div className="run-evidence-block">
                <div className="section-label">Resolved config delta</div>
                <dl className="metric-list">
                  {configEntries.map((c, i) => (
                    <React.Fragment key={i}>
                      <dt>{c[0]}</dt>
                      <dd>{c[1]}</dd>
                    </React.Fragment>
                  ))}
                  {configEntries.length === 0 && <span className="empty-state">No specific config parameters found.</span>}
                </dl>
              </div>
            </div>
          </section>

          {/* Canonical Artifacts Section */}
          {(artifacts.length > 0 || !run.path) && (
            <section className="artifact-panel">
              <div className="section-label">Artifact Explorer (Canonical)</div>
              <h3>Machine-readable outputs</h3>
              {artifacts.length ? (
                <div className="artifact-list">
                  {artifacts.map((artifact, i) => {
                    const href = buildRunArtifactHref(run.path, artifact.file_name);
                    return (
                      <button 
                        key={i}
                        className="artifact-link" 
                        type="button" 
                        title={`Open ${artifact.file_name}`}
                        onClick={() => {
                          // eslint-disable-next-line no-undef
                          if (typeof window.quantlabDesktop?.openExternal === 'function') {
                            // eslint-disable-next-line no-undef
                            window.quantlabDesktop.openExternal(href);
                          }
                        }}>
                        <span className="artifact-name-wrap">
                          <span className="artifact-icon">📄</span>
                          <span>{artifact.file_name}</span>
                        </span>
                        <span className="artifact-size">{formatBytes(artifact.size_bytes)}</span>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="empty-state">
                  No canonical artifact manifest available for this run.
                </div>
              )}
            </section>
          )}

          {/* Local Workspace / Output Path Section */}
          {run.path && (
            <section className="artifact-panel">
              <div className="section-label">Local Evidence (Workspace)</div>
              <h3>Artifact directory</h3>
              <div className="artifact-meta" style={{ marginBottom: '12px' }}>Path: {run.path}</div>
              {fileEntries.length ? (
                <div className="artifact-list">
                  {fileEntries.map((file, i) => {
                    const isDir = file.kind === 'directory';
                    return (
                      <button 
                        key={i} 
                        className="artifact-link"
                        type="button"
                        title={isDir ? `Open folder: ${file.name}` : `Open file: ${file.name}`}
                        onClick={() => {
                          // eslint-disable-next-line no-undef
                          if (typeof window.quantlabDesktop?.openPath === 'function') {
                            // eslint-disable-next-line no-undef
                            window.quantlabDesktop.openPath(file.path);
                          }
                        }}
                      >
                        <span className="artifact-name-wrap">
                          <span className="artifact-icon">{isDir ? '📁' : '📄'}</span>
                          <span>{file.name}{isDir ? '/' : ''}</span>
                        </span>
                        <span className="artifact-size">
                          {isDir ? 'dir' : (file.size_bytes != null ? formatBytes(file.size_bytes) : '')}
                        </span>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="empty-state">
                  The local workspace directory is empty or could not be listed.
                </div>
              )}
              {detail.directoryTruncated && (
                <div className="artifact-meta" style={{ marginTop: '8px', fontSize: '0.8rem' }}>
                  Listing truncated to first visible entries.
                </div>
              )}
            </section>
          )}

        </div>

        <aside className="run-detail-side run-evidence-rail stack">
          <section className="artifact-panel run-rail-card">
            <div className="section-label">Decision / validation</div>
            <h3>What should happen next</h3>
            <div className="run-row-flags">
              {isCandidate && <span className="badge candidate">Candidate</span>}
              {isShortlist && <span className="badge shortlist">Shortlist</span>}
              {isBaseline && <span className="badge baseline">Baseline</span>}
            </div>
            {hasDecisionPeers && (
              <div style={{ marginTop: '15px' }}>
                 <button className="ghost-btn" onClick={() => openTab({ kind: 'compare', runIds: decision.getDecisionCompareRunIds(), label: 'decision peers' })}>Compare peers</button>
              </div>
            )}
          </section>

          <section className="artifact-panel run-rail-card">
            <div className="section-label">Evidence continuity</div>
            <h3>Run outputs and links</h3>
            <dl className="metric-list compact">
              <dt>Window</dt><dd>{run.start || "-"} to {run.end || "-"}</dd>
              <dt>Output path</dt><dd className="mono-cell" style={{ fontSize: '0.8rem' }}>{run.path || "-"}</dd>
              <dt>Raw report</dt><dd>{detail.reportUrl ? "Available" : "Missing"}</dd>
              <dt>Launch review</dt><dd>{latestRelatedJob?.request_id || "None"}</dd>
            </dl>
            <div className="workflow-actions" style={{ marginTop: '12px' }}>
              {latestRelatedJob?.request_id && (
                <button className="ghost-btn" onClick={() => openTab('job', latestRelatedJob.request_id)}>
                  Open launch review
                </button>
              )}
              {detail.reportUrl && (
                <button className="ghost-btn" onClick={() => {
                  // eslint-disable-next-line no-undef
                  if (typeof window.quantlabDesktop?.openExternal === 'function') {
                    // eslint-disable-next-line no-undef
                    window.quantlabDesktop.openExternal(detail.reportUrl);
                  }
                }}>
                  Open report.json
                </button>
              )}
              {latestRelatedJob?.stderr_href && (
                <button className="ghost-btn" onClick={() => {
                  // eslint-disable-next-line no-undef
                  if (typeof window.quantlabDesktop?.openExternal === 'function') {
                    // eslint-disable-next-line no-undef
                    window.quantlabDesktop.openExternal(latestRelatedJob.stderr_href);
                  }
                }}>
                  Open stderr
                </button>
              )}
            </div>
          </section>

          <section className="artifact-panel run-rail-card">
            <div className="section-label">Sweep continuity</div>
            <h3>Decision lineage</h3>
            {sweepEntries.length ? (
              <ul style={{ paddingLeft: '15px', color: 'var(--muted)' }}>
                {sweepEntries.map((e, i) => <li key={i}>{e.sweep_id}</li>)}
              </ul>
            ) : (
              <div className="empty-state">No local sweep intent linked to this decision.</div>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, tone = '' }) {
  return (
    <article className={`summary-card ${tone || ''}`}>
      <div className="label">{label}</div>
      <div className={`value ${tone || ''}`}>{value}</div>
    </article>
  );
}
