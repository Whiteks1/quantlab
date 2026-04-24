import React, { useState } from 'react';
import type { LaunchTab } from '../../shared/models/tab';
import { formatDateTime, formatCount, titleCase } from '../modules/utils';
import { useQuantLab as _useQuantLab } from './QuantLabContext';

// QuantLabContext is a JS file; cast to any so strict-mode TSX can consume it.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const useQuantLab = _useQuantLab as () => any;

// ── Local helpers ─────────────────────────────────────────────────────────────

type Signal = { label: string; tone: string };

function launchSignal(status: string | undefined): Signal {
  const v = (status ?? '').toLowerCase();
  if (!v || v === 'none') return { label: 'Pending', tone: 'tone-warning' };
  if (v.includes('succeeded')) return { label: 'Completed', tone: 'tone-positive' };
  if (v.includes('failed')) return { label: 'Failed', tone: 'tone-negative' };
  if (v.includes('running') || v.includes('queued') || v.includes('pending')) return { label: 'In flight', tone: 'tone-warning' };
  return { label: titleCase(status ?? ''), tone: 'tone-warning' };
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SummaryCard({ label, value, tone = '' }: { label: string; value: string; tone?: string }) {
  return (
    <article className={`summary-card ${tone}`}>
      <div className="label">{label}</div>
      <div className={`value ${tone}`}>{value}</div>
    </article>
  );
}

function JobCard({ job, onOpen }: { job: any; onOpen: () => void }) {
  const sig = launchSignal(job.status);
  return (
    <button className="system-job-item" type="button" onClick={onOpen}>
      <div className="system-job-top">
        <strong>{titleCase(job.command ?? 'unknown')}</strong>
        <span className={sig.tone}>{sig.label}</span>
      </div>
      <div className="artifact-meta">
        {job.request_id ?? '-'}{job.run_id ? ` · ${job.run_id}` : ''}
      </div>
      <div className="artifact-meta">
        {job.summary ?? 'No summary'} · {formatDateTime(job.created_at ?? job.started_at)}
      </div>
    </button>
  );
}

// ── Quick-launch form ─────────────────────────────────────────────────────────

function QuickLaunchForm({ serverUrl, onRefresh }: { serverUrl: string | null; onRefresh: () => void }) {
  const [command, setCommand] = useState<'run' | 'sweep'>('sweep');
  const [configPath, setConfigPath] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setStatus('Submitting…');
    try {
      const params: Record<string, string> = {};
      if (command === 'sweep' && configPath.trim()) params.config_path = configPath.trim();
      const result = await window.quantlabDesktop.postJson('/api/launch-control', { command, params }) as any;
      setStatus(result?.message ?? 'Launch accepted.');
      setConfigPath('');
      await onRefresh();
    } catch (err: any) {
      setStatus(`Error: ${err?.message ?? 'Launch failed.'}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="artifact-panel">
      <div className="section-label">Quick launch</div>
      <h3>Submit a new job</h3>
      <form className="launch-form" onSubmit={handleSubmit}>
        <div className="launch-form-row">
          <label className="launch-label">Command</label>
          <div className="workflow-actions">
            <button
              type="button"
              className={`ghost-btn ${command === 'run' ? 'is-selected' : ''}`}
              onClick={() => setCommand('run')}
            >
              Run
            </button>
            <button
              type="button"
              className={`ghost-btn ${command === 'sweep' ? 'is-selected' : ''}`}
              onClick={() => setCommand('sweep')}
            >
              Sweep
            </button>
          </div>
        </div>
        {command === 'sweep' && (
          <div className="launch-form-row">
            <label className="launch-label" htmlFor="launch-config-path">Config path</label>
            <input
              id="launch-config-path"
              className="launch-input"
              type="text"
              placeholder="configs/experiments/my_config.yaml"
              value={configPath}
              onChange={(e) => setConfigPath(e.target.value)}
              disabled={busy}
            />
          </div>
        )}
        <div className="workflow-actions" style={{ marginTop: '12px' }}>
          <button className="ghost-btn" type="submit" disabled={busy || (command === 'sweep' && !configPath.trim())}>
            {busy ? 'Submitting…' : 'Submit'}
          </button>
          {serverUrl && (
            <button
              className="ghost-btn"
              type="button"
              onClick={() => {
                if (typeof window.quantlabDesktop?.openExternal === 'function') {
                  window.quantlabDesktop.openExternal(`${serverUrl.replace(/\/$/, '')}/research_ui/index.html#/launch`);
                }
              }}
            >
              Full browser form
            </button>
          )}
        </div>
        {status && <div className={`ops-callout ${status.startsWith('Error') ? 'tone-negative' : 'tone-positive'}`} style={{ marginTop: '10px' }}>{status}</div>}
      </form>
    </section>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function LaunchPane({ tab: _tab }: { tab: LaunchTab }) {
  const ctx = useQuantLab();
  const { state, getJobs, getLatestRun, getLatestFailedJob, openTab, refresh } = ctx;

  const snapshot = state.snapshot ?? {};
  const launchControl = (snapshot as any).launchControl ?? null;
  const serverUrl: string | null = state.workspace?.serverUrl ?? null;

  const allJobs: any[] = getJobs();
  const recentJobs: any[] = allJobs.slice(0, 10);
  const latestRun = getLatestRun();
  const latestFailedJob = getLatestFailedJob();
  const totalJobs: number = Array.isArray(launchControl?.jobs) ? launchControl.jobs.length : 0;
  const failedCount = allJobs.filter((j: any) => (j.status ?? '').toLowerCase().includes('failed')).length;
  const inFlightCount = allJobs.filter((j: any) => {
    const s = (j.status ?? '').toLowerCase();
    return s.includes('running') || s.includes('queued') || s.includes('pending');
  }).length;

  const openExternal = (path: string) => {
    const base = serverUrl ? serverUrl.replace(/\/$/, '') : '';
    if (typeof window.quantlabDesktop?.openExternal === 'function') {
      window.quantlabDesktop.openExternal(`${base}${path}`);
    }
  };

  return (
    <div className="tab-shell launch-pane">
      {/* Header */}
      <div className="artifact-top">
        <div>
          <div className="section-label">Launch control</div>
          <h3>Launch</h3>
          <div className="artifact-meta">
            Primary launch surface for run and sweep execution, queue review, and job log inspection.
            Browser runtime remains available only as a secondary bridge.
          </div>
        </div>
        <div className="artifact-actions">
          {serverUrl && (
            <button className="ghost-btn" type="button" onClick={() => openExternal('/research_ui/index.html#/launch')}>
              Open browser bridge
            </button>
          )}
          {latestRun?.run_id && (
            <button className="ghost-btn" type="button" onClick={() => openTab({ kind: 'run', runId: latestRun.run_id })}>
              Latest run
            </button>
          )}
          {recentJobs[0]?.request_id && (
            <button className="ghost-btn" type="button" onClick={() => openTab({ kind: 'job', requestId: recentJobs[0].request_id })}>
              Latest job
            </button>
          )}
        </div>
      </div>

      {/* Summary cards */}
      <div className="tab-summary-grid">
        <SummaryCard
          label="Total jobs"
          value={formatCount(totalJobs)}
          tone={totalJobs ? 'tone-positive' : 'tone-warning'}
        />
        <SummaryCard
          label="In flight"
          value={formatCount(inFlightCount)}
          tone={inFlightCount ? 'tone-warning' : ''}
        />
        <SummaryCard
          label="Failed"
          value={formatCount(failedCount)}
          tone={failedCount ? 'tone-negative' : 'tone-positive'}
        />
        <SummaryCard
          label="Latest run"
          value={latestRun?.run_id ?? 'None'}
          tone={latestRun?.run_id ? 'tone-positive' : 'tone-warning'}
        />
        <SummaryCard
          label="Browser bridge"
          value={serverUrl ? 'Available' : 'Unavailable'}
          tone={serverUrl ? 'tone-positive' : 'tone-warning'}
        />
      </div>

      {/* Failed job callout */}
      {latestFailedJob && (
        <div className="ops-callout tone-warning" style={{ marginBottom: '16px' }}>
          Latest failed job: <strong>{latestFailedJob.request_id ?? '-'}</strong>
          {' · '}{titleCase(latestFailedJob.command ?? 'unknown')}
          <button
            className="ghost-btn mini"
            type="button"
            style={{ marginLeft: '12px' }}
            onClick={() => openTab({ kind: 'job', requestId: latestFailedJob.request_id })}
          >
            Review
          </button>
        </div>
      )}

      {/* Launch queue + quick-launch form */}
      <div className="artifact-grid">
        <section className="artifact-panel">
          <div className="section-label">Launch queue</div>
          <h3>Recent jobs</h3>
          {recentJobs.length ? (
            <div className="system-job-list">
              {recentJobs.map((job: any) => (
                <JobCard
                  key={job.request_id}
                  job={job}
                  onOpen={() => openTab({ kind: 'job', requestId: job.request_id })}
                />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              No launch jobs are visible yet. Submit a run or sweep to get started.
            </div>
          )}
        </section>

        <QuickLaunchForm serverUrl={serverUrl} onRefresh={refresh} />
      </div>
    </div>
  );
}
