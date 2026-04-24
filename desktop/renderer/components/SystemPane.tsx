import React, { useMemo } from 'react';
import type { SystemTab } from '../../shared/models/tab';
import type { WorkspaceState } from '../../shared/models/workspace';
import type { SnapshotStatus } from '../../shared/models/snapshot';
import { useQuantLab as _useQuantLab } from './QuantLabContext';

// QuantLabContext is a JS file; cast to any so strict-mode TSX can consume it.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const useQuantLab = _useQuantLab as () => any;

// ── Local formatting utilities ────────────────────────────────────────────────

function fmt(n: number | null | undefined): string {
  if (n == null || isNaN(Number(n))) return '0';
  return String(Number(n));
}

function titleCase(s: string): string {
  return s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return 'Never';
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function truncate(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text;
  return '…' + text.slice(text.length - maxChars);
}

// ── Signal resolvers (ported from tab-renderers.js) ──────────────────────────

type Signal = { label: string; tone: string };

function workspaceSignal(ws: Partial<WorkspaceState>): Signal {
  if (ws.status === 'ready') return { label: 'Attached', tone: 'tone-positive' };
  if (ws.status === 'starting') return { label: 'Booting', tone: 'tone-warning' };
  if (ws.status === 'error' || ws.status === 'stopped') return { label: 'Review required', tone: 'tone-negative' };
  return { label: 'Pending', tone: 'tone-warning' };
}

function snapshotSignal(ss: Partial<SnapshotStatus>): Signal & { lastSuccessAt: string } {
  const last = fmtDate(ss.lastSuccessAt);
  if (ss.status === 'ok') return { label: ss.refreshPaused ? 'Paused' : 'Live', tone: ss.refreshPaused ? 'tone-warning' : 'tone-positive', lastSuccessAt: last };
  if (ss.status === 'degraded') return { label: ss.refreshPaused ? 'Review required' : 'Degraded', tone: 'tone-warning', lastSuccessAt: last };
  if (ss.status === 'error') return { label: ss.refreshPaused ? 'Review required' : 'Unavailable', tone: 'tone-negative', lastSuccessAt: last };
  return { label: 'Waiting', tone: 'tone-warning', lastSuccessAt: last };
}

function launchSignal(status: string | undefined): Signal {
  const v = (status ?? '').toLowerCase();
  if (!v || v === 'none') return { label: 'Pending', tone: 'tone-warning' };
  if (v.includes('succeeded')) return { label: 'Completed', tone: 'tone-positive' };
  if (v.includes('failed')) return { label: 'Failed', tone: 'tone-negative' };
  if (v.includes('running') || v.includes('queued') || v.includes('pending')) return { label: 'In flight', tone: 'tone-warning' };
  return { label: titleCase(status ?? ''), tone: 'tone-warning' };
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SummaryCard({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <article className={`summary-card ${tone}`}>
      <div className="label" title={label}>{label}</div>
      <div className={`value ${tone}`} title={value}>{value}</div>
    </article>
  );
}

function MetricRow({ label, value, tone = '' }: { label: string; value: string; tone?: string }) {
  return (
    <div className={tone}>
      <dt title={label}>{label}</dt>
      <dd title={value}>{value}</dd>
    </div>
  );
}

function WatchItem({ tone, label, body }: { tone: string; label: string; body: string }) {
  return (
    <article className={`system-watch-item tone-${tone}`}>
      <strong>{label}</strong>
      <p>{body}</p>
    </article>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function SystemPane({ tab: _tab }: { tab: SystemTab }) {
  const ctx = useQuantLab();
  const { state, getRuns, getLatestRun, getLatestFailedJob, findJob, decision, openTab } = ctx;

  const workspace: Partial<WorkspaceState> = state.workspace ?? {};
  const snapshotStatus: Partial<SnapshotStatus> = state.snapshotStatus ?? {};
  const snapshot = state.snapshot ?? {};
  const launchControl = (snapshot as any).launchControl ?? null;
  const paper = (snapshot as any).paperHealth ?? null;
  const broker = (snapshot as any).brokerHealth ?? null;
  const stepbit = (snapshot as any).stepbitWorkspace ?? null;
  const liveUrls: Record<string, unknown> = stepbit?.live_urls ?? {};

  const runs = getRuns();
  const jobs: any[] = Array.isArray(launchControl?.jobs) ? launchControl.jobs.slice(0, 5) : [];
  const latestRun = getLatestRun();
  const latestFailedJob = getLatestFailedJob();
  const candidateEntries = decision.getCandidateEntriesResolved();
  const shortlistCount = candidateEntries.filter((e: any) => e.shortlisted && e.run).length;
  const brokerAlerts: any[] = Array.isArray(broker?.alerts) ? broker.alerts : [];
  const store = state.candidatesStore ?? {};

  const wsSig = workspaceSignal(workspace);
  const ssSig = snapshotSignal(snapshotStatus);

  const logPreview = useMemo(() => {
    const logs: string[] = Array.isArray(workspace.logs) ? workspace.logs.filter((l) => typeof l === 'string' && l.trim()) : [];
    if (!logs.length) return '';
    return truncate(logs.slice(-12).join('\n'), 500);
  }, [workspace.logs]);

  const systemUrls = useMemo(() => {
    const entries: { label: string; url: string }[] = [];
    if (workspace.serverUrl) {
      entries.push({ label: 'Research UI', url: `${workspace.serverUrl.replace(/\/$/, '')}/research_ui/index.html` });
    }
    Object.entries(liveUrls).forEach(([key, value]) => {
      if (typeof value === 'string' && /^https?:\/\//i.test(value)) {
        entries.push({ label: titleCase(key.replace(/_/g, ' ')), url: value });
      }
    });
    return entries;
  }, [workspace.serverUrl, liveUrls]);

  const watchItems = useMemo(() => {
    const items: { tone: string; label: string; body: string }[] = [];
    const localFallback = snapshotStatus.source === 'local';
    if (workspace.error) {
      items.push({ tone: 'negative', label: 'Workspace error', body: workspace.error });
    } else {
      items.push({
        tone: workspace.status === 'ready' ? 'positive' : 'warning',
        label: 'Workspace bootstrap',
        body: localFallback
          ? 'research_ui is not reachable; the desktop is running from local artifacts.'
          : workspace.status === 'ready'
            ? 'Research UI is reachable from the desktop shell.'
            : 'Bootstrap is incomplete or waiting for the local server.',
      });
    }
    if (snapshotStatus.status === 'error') {
      items.push({ tone: 'negative', label: 'Snapshot refresh', body: snapshotStatus.error ?? 'The local API refresh loop is currently degraded.' });
    }
    if (latestFailedJob) {
      items.push({ tone: 'warning', label: 'Latest failed launch', body: `${(latestFailedJob as any).request_id ?? '-'} · ${titleCase((latestFailedJob as any).command ?? 'unknown')} should be reviewed before trusting the current path.` });
    } else {
      items.push({ tone: jobs.length ? 'positive' : 'neutral', label: 'Launch review', body: jobs.length ? 'No failed launch is visible in the tracked recent jobs.' : 'No launch activity is visible yet.' });
    }
    if (brokerAlerts.length) {
      items.push({ tone: 'negative', label: 'Broker boundary', body: brokerAlerts.slice(0, 2).map((a: any) => a.code ?? a.session_id ?? 'alert').join(' | ') });
    } else {
      items.push({ tone: 'positive', label: 'Broker boundary', body: 'No broker alerts are currently surfaced.' });
    }
    if (!liveUrls.frontend_reachable) {
      items.push({ tone: 'warning', label: 'Stepbit frontend', body: 'Stepbit frontend is not currently reachable via live URLs.' });
    }
    return items;
  }, [workspace, snapshotStatus, brokerAlerts, latestFailedJob, jobs, liveUrls]);

  const handleExternalClick = (url: string) => {
    if (typeof window.quantlabDesktop?.openExternal === 'function') {
      window.quantlabDesktop.openExternal(url);
    }
  };

  return (
    <div className="tab-shell system-pane">
      {/* Header */}
      <div className="artifact-top">
        <div>
          <div className="section-label">Runtime diagnostics</div>
          <h3>System</h3>
          <div className="artifact-meta">Native runtime inventory for bootstrap state, API refresh, launch visibility, and workspace continuity.</div>
        </div>
        <div className="artifact-actions">
          {workspace.serverUrl && (
            <button className="ghost-btn" onClick={() => handleExternalClick(`${workspace.serverUrl!.replace(/\/$/, '')}/research_ui/index.html`)}>
              Open research_ui
            </button>
          )}
          {latestRun && (
            <button className="ghost-btn" onClick={() => openTab({ kind: 'run', runId: (latestRun as any).run_id })}>
              Latest run
            </button>
          )}
          {jobs[0]?.request_id && (
            <button className="ghost-btn" onClick={() => openTab({ kind: 'job', requestId: jobs[0].request_id })}>
              Latest launch review
            </button>
          )}
        </div>
      </div>

      {/* Summary cards */}
      <div className="tab-summary-grid">
        <SummaryCard label="QuantLab" value={wsSig.label} tone={wsSig.tone} />
        <SummaryCard label="Snapshot" value={ssSig.label} tone={ssSig.tone} />
        <SummaryCard label="Indexed runs" value={fmt(runs.length)} tone={runs.length ? 'tone-positive' : 'tone-warning'} />
        <SummaryCard label="Launch jobs" value={fmt(Array.isArray(launchControl?.jobs) ? launchControl.jobs.length : 0)} tone={jobs.length ? 'tone-positive' : 'tone-warning'} />
        <SummaryCard label="Paper state" value={paper?.available ? 'Ready' : 'Pending'} tone={paper?.available ? 'tone-positive' : 'tone-warning'} />
        <SummaryCard label="Broker alerts" value={fmt(brokerAlerts.length)} tone={brokerAlerts.length ? 'tone-negative' : broker?.available ? 'tone-positive' : 'tone-warning'} />
        <SummaryCard label="Launch browser" value={workspace.serverUrl ? 'Available' : 'Unavailable'} tone={workspace.serverUrl ? 'tone-positive' : 'tone-warning'} />
        <SummaryCard label="Stepbit frontend" value={liveUrls.frontend_reachable ? 'Attached' : 'Detached'} tone={liveUrls.frontend_reachable ? 'tone-positive' : 'tone-warning'} />
        <SummaryCard label="Stepbit core" value={liveUrls.core_ready ? 'Ready' : liveUrls.core_reachable ? 'Partial' : 'Detached'} tone={liveUrls.core_ready ? 'tone-positive' : liveUrls.core_reachable ? 'tone-warning' : 'tone-negative'} />
      </div>

      {/* Main grid */}
      <div className="artifact-grid system-grid">
        {/* Workspace bootstrap */}
        <section className="artifact-panel system-stack">
          <div className="section-label">Workspace</div>
          <h3>Bootstrap and refresh state</h3>
          <dl className="metric-list compact">
            <MetricRow label="Workspace state" value={wsSig.label} tone={wsSig.tone} />
            <MetricRow label="Server URL" value={workspace.serverUrl ?? 'pending'} />
            <MetricRow label="Server source" value={titleCase(workspace.source ?? 'unknown')} />
            <MetricRow label="Launch browser surface" value={workspace.serverUrl ? 'Available (browser transitional)' : 'Unavailable (runtime offline)'} tone={workspace.serverUrl ? 'tone-positive' : 'tone-warning'} />
            <MetricRow label="Refresh state" value={ssSig.label} tone={ssSig.tone} />
            <MetricRow label="Last refresh" value={ssSig.lastSuccessAt} />
            <MetricRow label="Consecutive refresh errors" value={fmt(snapshotStatus.consecutiveErrors ?? 0)} />
            <MetricRow label="Refresh mode" value={snapshotStatus.refreshPaused ? 'Paused' : 'Active'} tone={snapshotStatus.refreshPaused ? 'tone-warning' : 'tone-positive'} />
            <MetricRow label="Workspace logs" value={fmt(Array.isArray(workspace.logs) ? workspace.logs.length : 0)} />
          </dl>
          {workspace.error && <div className="ops-callout tone-negative">{workspace.error}</div>}
        </section>

        {/* Reachable surfaces */}
        <section className="artifact-panel system-stack">
          <div className="section-label">Surfaces</div>
          <h3>Reachable local interfaces</h3>
          {systemUrls.length ? (
            <div className="system-link-list">
              {systemUrls.map((entry) => (
                <button key={entry.url} className="system-link-item" type="button" onClick={() => handleExternalClick(entry.url)}>
                  <strong>{entry.label}</strong>
                  <span>{entry.url}</span>
                </button>
              ))}
            </div>
          ) : (
            <div className="empty-state">No addressable browser surfaces are visible yet. This is expected while runtime is booting or when the shell is running local-only fallback.</div>
          )}
        </section>

        {/* Launch queue */}
        <section className="artifact-panel system-stack">
          <div className="section-label">Launch queue</div>
          <h3>Recent tracked jobs</h3>
          {jobs.length ? (
            <div className="system-job-list">
              {jobs.map((job: any) => {
                const sig = launchSignal(job.status);
                return (
                  <button key={job.request_id} className="system-job-item" type="button" onClick={() => openTab({ kind: 'job', requestId: job.request_id })}>
                    <div className="system-job-top">
                      <strong>{titleCase(job.command ?? 'unknown')}</strong>
                      <span className={sig.tone}>{sig.label}</span>
                    </div>
                    <div className="artifact-meta">{job.request_id ?? '-'}{job.run_id ? ` · ${job.run_id}` : ''}</div>
                    <div className="artifact-meta">{job.summary ?? 'No summary'} · {fmtDate(job.created_at ?? job.started_at)}</div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="empty-state">No launch jobs are available yet. This is expected before the first run or sweep request.</div>
          )}
        </section>

        {/* Decision memory */}
        <section className="artifact-panel system-stack">
          <div className="section-label">Decision memory</div>
          <h3>Local selection state</h3>
          <dl className="metric-list compact">
            <MetricRow label="Candidates" value={fmt(candidateEntries.length)} />
            <MetricRow label="Shortlisted" value={fmt(shortlistCount)} />
            <MetricRow label="Baseline" value={(store as any).baseline_run_id ?? 'none'} />
            <MetricRow label="Latest run" value={(latestRun as any)?.run_id ?? 'none'} />
            <MetricRow label="Latest failed launch" value={(latestFailedJob as any)?.request_id ?? 'none'} />
          </dl>
        </section>
      </div>

      {/* Attention + logs row */}
      <div className="artifact-grid system-grid">
        <section className="artifact-panel system-stack">
          <div className="section-label">Attention</div>
          <h3>What needs operator review</h3>
          <div className="system-watch-list">
            {watchItems.map((item, i) => (
              <WatchItem key={i} tone={item.tone} label={item.label} body={item.body} />
            ))}
          </div>
        </section>

        <section className="artifact-panel system-stack">
          <div className="section-label">Workspace logs</div>
          <h3>Latest bootstrap output</h3>
          {logPreview
            ? <pre className="system-log">{logPreview}</pre>
            : <div className="empty-state">No workspace log lines have been captured yet.</div>
          }
        </section>
      </div>
    </div>
  );
}
