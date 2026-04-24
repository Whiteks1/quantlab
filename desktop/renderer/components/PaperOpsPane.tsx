import React, { useMemo } from 'react';
import type { PaperTab } from '../../shared/models/tab';
import { formatDateTime, formatCount, titleCase } from '../modules/utils';
import { useQuantLab as _useQuantLab } from './QuantLabContext';

// QuantLabContext is a JS file; cast to any so strict-mode TSX can consume it.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const useQuantLab = _useQuantLab as () => any;

// ── Local helpers ─────────────────────────────────────────────────────────────

type Signal = { label: string; tone: string };

function resolveLaunchSignal(value: string | undefined, emptyLabel = 'Launch pending'): Signal {
  const v = (value ?? '').toLowerCase();
  if (!v || v === 'none' || v.includes('no linked')) return { label: emptyLabel, tone: 'tone-warning' };
  if (v.includes('succeeded')) return { label: 'Completed', tone: 'tone-positive' };
  if (v.includes('failed')) return { label: 'Failed', tone: 'tone-negative' };
  if (v.includes('running') || v.includes('queued') || v.includes('pending')) return { label: 'In flight', tone: 'tone-warning' };
  if (v.includes('unknown')) return { label: 'Review state', tone: 'tone-warning' };
  return { label: titleCase(value ?? ''), tone: 'tone-warning' };
}

function selectNextAction({
  paper, broker, latestFailedJob, latestJob, latestRun, decisionCompareRunIds, baselineRunId,
}: any): { tone: string; message: string } {
  if (latestFailedJob) return { tone: 'warning', message: `Start by reviewing failed launch ${latestFailedJob.request_id || '-'}. Paper health may look stable while the newest launch path is still broken.` };
  if (broker?.has_alerts) return { tone: 'negative', message: 'Broker alerts are present. Inspect the broker boundary before trusting any submission-ready flow.' };
  if (decisionCompareRunIds.length >= 2) return { tone: 'positive', message: 'You already have enough decision runs to compare. Use shortlist compare and decide whether to keep or replace the current baseline.' };
  if (latestRun?.run_id) return { tone: 'neutral', message: `Open the latest run ${latestRun.run_id} and inspect its artifacts before promoting anything toward paper.` };
  if (paper?.available && paper?.total_sessions) return { tone: 'neutral', message: `Paper health is visible with ${paper.total_sessions} tracked sessions. Next useful step is to connect that visibility back to a concrete run or decision candidate.` };
  if (latestJob) return { tone: 'neutral', message: `Recent launch activity exists (${latestJob.request_id || '-'}) but paper continuity is still thin. Review the job and then the resulting run.` };
  if (baselineRunId) return { tone: 'neutral', message: `A baseline run is pinned (${baselineRunId}). Open it and decide whether it should remain the reference before launching new paper work.` };
  return { tone: 'warning', message: 'Paper Ops is ready, but there is not enough operational history yet. Launch a run or sweep first, then come back here to review continuity.' };
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

function MetricRow({ label, value, tone = '' }: { label: string; value: string; tone?: string }) {
  return (
    <div className={tone}>
      <dt title={label}>{label}</dt>
      <dd title={value}>{value}</dd>
    </div>
  );
}

function OpsChipRow({ label, counts }: { label: string; counts: Record<string, unknown> | null | undefined }) {
  const entries = Object.entries(counts ?? {}).filter(([, v]) => Number(v) > 0);
  if (!entries.length) return null;
  return (
    <div className="ops-chip-row">
      <div className="eyebrow">{label}</div>
      <div className="run-row-flags">
        {entries.map(([key, value]) => (
          <span key={key} className="metric-chip">
            {titleCase(key.replace(/_/g, ' '))} {formatCount(Number(value))}
          </span>
        ))}
      </div>
    </div>
  );
}

function NowCard({ tone, label, title, meta }: { tone: string; label: string; title: string; meta: string }) {
  return (
    <article className={`ops-state-card tone-${tone || 'neutral'}`}>
      <div className="eyebrow">{label}</div>
      <strong>{title}</strong>
      <p>{meta}</p>
    </article>
  );
}

function WatchCard({ tone, label, body }: { tone: string; label: string; body: string }) {
  return (
    <article className={`ops-watch-item tone-${tone || 'neutral'}`}>
      <strong>{label}</strong>
      <p>{body}</p>
    </article>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function PaperOpsPane({ tab: _tab }: { tab: PaperTab }) {
  const ctx = useQuantLab();
  const { state, getJobs, getLatestRun, getLatestFailedJob, findJob, decision, openTab } = ctx;

  const snapshot = state.snapshot ?? {};
  const paper = (snapshot as any).paperHealth ?? null;
  const broker = (snapshot as any).brokerHealth ?? null;
  const stepbit = (snapshot as any).stepbitWorkspace ?? null;
  const liveUrls = stepbit?.live_urls ?? {};
  const store = state.candidatesStore ?? {};
  const serverUrl: string | null = state.workspace?.serverUrl ?? null;

  const jobs: any[] = Array.isArray((snapshot as any).launchControl?.jobs)
    ? (snapshot as any).launchControl.jobs
    : [];
  const latestJob = getJobs()[0] ?? null;
  const latestFailedJob = getLatestFailedJob();
  const latestRun = getLatestRun();
  const decisionCompareRunIds: string[] = decision.getDecisionCompareRunIds?.() ?? [];
  const candidateEntries: any[] = decision.getCandidateEntriesResolved();
  const shortlistCount = candidateEntries.filter((e: any) => e.shortlisted && e.run).length;
  const baselineRunId: string = store?.baseline_run_id ?? '';

  const paperReady = Boolean(paper?.available && paper?.total_sessions);
  const brokerReady = Boolean(broker?.available);
  const brokerHasAlerts = Boolean(broker?.has_alerts);
  const stepbitLive = Boolean(liveUrls?.frontend_reachable && liveUrls?.backend_reachable);

  const nowItems = useMemo(() => [
    {
      tone: paperReady ? 'positive' : 'warning',
      label: 'Paper track',
      title: paperReady
        ? `${paper.total_sessions} sessions tracked`
        : 'No paper sessions tracked yet (not blocked)',
      meta: paper?.latest_session_status
        ? `Latest status ${titleCase(paper.latest_session_status)}${paper?.latest_session_at ? ` · ${formatDateTime(paper.latest_session_at)}` : ''}`
        : 'Paper execution has not produced visible sessions yet.',
    },
    {
      tone: brokerHasAlerts ? 'negative' : brokerReady ? 'positive' : 'warning',
      label: 'Broker boundary',
      title: brokerHasAlerts
        ? 'Broker alerts require review'
        : brokerReady
          ? 'Broker validations are visible'
          : 'Broker validations not present yet (not blocked)',
      meta: brokerHasAlerts
        ? `${formatCount((broker?.alerts ?? []).length)} active alerts across the submission boundary.`
        : brokerReady
          ? `${formatCount(broker?.total_sessions ?? 0)} broker validation sessions indexed.`
          : broker?.message ?? 'No broker order-validation surface is indexed yet.',
    },
    {
      tone: decisionCompareRunIds.length >= 2 ? 'positive' : candidateEntries.length ? 'warning' : '',
      label: 'Decision queue',
      title: decisionCompareRunIds.length >= 2
        ? `${decisionCompareRunIds.length} runs ready to compare`
        : candidateEntries.length
          ? 'Decision memory is partial'
          : 'No decision queue yet',
      meta: `Candidates ${formatCount(candidateEntries.length)} · Shortlist ${formatCount(shortlistCount)} · Baseline ${baselineRunId || 'none'}`,
    },
  ], [paper, broker, paperReady, brokerReady, brokerHasAlerts, decisionCompareRunIds, candidateEntries, shortlistCount, baselineRunId]);

  const watchItems = useMemo(() => [
    paper?.latest_issue_session_id
      ? { tone: 'negative', label: 'Paper issue', body: `${paper.latest_issue_session_id}${paper?.latest_issue_error_type ? ` · ${paper.latest_issue_error_type}` : ''}` }
      : { tone: 'positive', label: 'Paper issue watch', body: 'No failing paper session is currently surfaced.' },
    brokerHasAlerts
      ? { tone: 'negative', label: 'Broker alerts', body: (broker?.alerts ?? []).slice(0, 2).map((a: any) => `${a.code || 'alert'}${a.session_id ? ` · ${a.session_id}` : ''}`).join(' | ') }
      : { tone: brokerReady ? 'positive' : 'warning', label: 'Broker alert watch', body: brokerReady ? 'No broker alerts are active right now.' : 'Broker alerting will appear here once validations exist.' },
    latestFailedJob
      ? { tone: 'warning', label: 'Latest failed launch', body: `${latestFailedJob.request_id || '-'} · ${titleCase(latestFailedJob.command || 'unknown')}${latestFailedJob?.ended_at ? ` · ${formatDateTime(latestFailedJob.ended_at)}` : ''}` }
      : { tone: 'positive', label: 'Launch failure watch', body: 'No failed launch job is currently visible in the recent job window.' },
    {
      tone: liveUrls?.core_ready ? 'positive' : stepbitLive ? 'warning' : '',
      label: 'Optional Stepbit boundary',
      body: liveUrls?.core_ready
        ? 'Stepbit app and core are available as an optional copiloted layer.'
        : stepbitLive
          ? 'Stepbit app is reachable but chat is not ready because core is unavailable.'
          : 'Stepbit remains optional and currently inactive from the shell perspective.',
    },
  ], [paper, broker, brokerReady, brokerHasAlerts, latestFailedJob, liveUrls, stepbitLive]);

  const nextAction = useMemo(() => selectNextAction({
    paper, broker, latestFailedJob, latestJob, latestRun, decisionCompareRunIds, baselineRunId,
  }), [paper, broker, latestFailedJob, latestJob, latestRun, decisionCompareRunIds, baselineRunId]);

  const openExternal = (path: string) => {
    const base = serverUrl ? serverUrl.replace(/\/$/, '') : '';
    if (typeof window.quantlabDesktop?.openExternal === 'function') {
      window.quantlabDesktop.openExternal(`${base}${path}`);
    }
  };

  const launchSig = resolveLaunchSignal(latestJob?.status);

  return (
    <div className="tab-shell paper-ops-pane">
      {/* Header */}
      <div className="artifact-top">
        <div>
          <div className="section-label">Operational surface</div>
          <h3>Paper ops</h3>
          <div className="artifact-meta">
            Runtime continuity for paper readiness, broker boundary, launch review, and decision
            follow-through.
          </div>
        </div>
        <div className="workflow-actions">
          <button className="ghost-btn" type="button" onClick={() => openExternal('/research_ui/index.html#/ops')}>
            Browser ops
          </button>
          {latestJob && (
            <button className="ghost-btn" type="button" onClick={() => openTab({ kind: 'job', requestId: latestJob.request_id })}>
              Latest launch review
            </button>
          )}
          {latestRun?.run_id && (
            <button className="ghost-btn" type="button" onClick={() => openTab({ kind: 'run', runId: latestRun.run_id })}>
              Latest run
            </button>
          )}
          {latestRun?.run_id && (
            <button className="ghost-btn" type="button" onClick={() => openTab({ kind: 'artifacts', runId: latestRun.run_id })}>
              Latest artifacts
            </button>
          )}
        </div>
      </div>

      {/* Summary cards */}
      <div className="tab-summary-grid">
        <SummaryCard label="Paper state" value={paperReady ? 'Ready' : 'No sessions yet'} tone={paperReady ? 'tone-positive' : 'tone-warning'} />
        <SummaryCard label="Latest paper state" value={titleCase(paper?.latest_session_status || 'none')} tone={paper?.latest_issue_session_id ? 'tone-negative' : paperReady ? 'tone-positive' : 'tone-warning'} />
        <SummaryCard label="Broker boundary" value={brokerReady ? 'Visible' : 'No validations yet'} tone={brokerHasAlerts ? 'tone-negative' : brokerReady ? 'tone-positive' : 'tone-warning'} />
        <SummaryCard label="Broker alerts" value={broker?.has_alerts ? 'Review required' : 'Clear'} tone={broker?.has_alerts ? 'tone-negative' : 'tone-positive'} />
        <SummaryCard label="Decision compare" value={decisionCompareRunIds.length >= 2 ? 'Ready' : 'Incomplete'} tone={decisionCompareRunIds.length >= 2 ? 'tone-positive' : 'tone-warning'} />
        <SummaryCard label="Latest failed launch" value={latestFailedJob ? 'Review required' : 'Clear'} tone={latestFailedJob ? 'tone-warning' : 'tone-positive'} />
        <SummaryCard label="Stepbit frontend" value={liveUrls?.frontend_reachable ? 'Attached' : 'Detached'} tone={liveUrls?.frontend_reachable ? 'tone-positive' : 'tone-negative'} />
        <SummaryCard label="Stepbit core" value={liveUrls?.core_ready ? 'Ready' : liveUrls?.core_reachable ? 'Partial' : 'Detached'} tone={liveUrls?.core_ready ? 'tone-positive' : liveUrls?.core_reachable ? 'tone-warning' : 'tone-negative'} />
      </div>

      {/* Now / Watch */}
      <div className="artifact-grid">
        <section className="artifact-panel">
          <div className="section-label">Now</div>
          <h3>Current operational picture</h3>
          <div className="ops-state-list">
            {nowItems.map((item, i) => <NowCard key={i} {...item} />)}
          </div>
        </section>
        <section className="artifact-panel">
          <div className="section-label">Watch</div>
          <h3>Items worth attention</h3>
          <div className="ops-watch-list">
            {watchItems.map((item, i) => <WatchCard key={i} {...item} />)}
          </div>
        </section>
      </div>

      {/* Next */}
      <section className="artifact-panel ops-next-panel">
        <div className="section-label">Next</div>
        <h3>Suggested next move</h3>
        <div className={`ops-callout tone-${nextAction.tone}`}>{nextAction.message}</div>
        <div className="workflow-actions">
          {latestFailedJob && (
            <button className="ghost-btn" type="button" onClick={() => openTab({ kind: 'job', requestId: latestFailedJob.request_id })}>
              Review failed launch
            </button>
          )}
          {latestRun?.run_id && (
            <button className="ghost-btn" type="button" onClick={() => openTab({ kind: 'run', runId: latestRun.run_id })}>
              Open latest run
            </button>
          )}
          {latestRun?.run_id && (
            <button className="ghost-btn" type="button" onClick={() => openTab({ kind: 'artifacts', runId: latestRun.run_id })}>
              Open latest artifacts
            </button>
          )}
          {decisionCompareRunIds.length >= 2 && (
            <button className="ghost-btn" type="button" onClick={() => openTab({ kind: 'compare', runIds: decisionCompareRunIds, label: 'decision runs' })}>
              Open decision compare
            </button>
          )}
          {baselineRunId && (
            <button className="ghost-btn" type="button" onClick={() => openTab({ kind: 'run', runId: baselineRunId })}>
              Open baseline
            </button>
          )}
          <button className="ghost-btn" type="button" onClick={() => openExternal('/research_ui/index.html#/ops')}>
            Browser ops
          </button>
        </div>
      </section>

      {/* Paper + Broker health */}
      <div className="artifact-grid">
        <section className="artifact-panel">
          <div className="section-label">Paper boundary</div>
          <h3>Session health</h3>
          <dl className="metric-list compact">
            <MetricRow label="Root" value={paper?.root_dir || '-'} />
            <MetricRow label="Latest session" value={paper?.latest_session_id || '-'} />
            <MetricRow label="Latest issue" value={paper?.latest_issue_session_id || '-'} />
            <MetricRow label="Latest issue type" value={paper?.latest_issue_error_type || '-'} />
          </dl>
          <OpsChipRow label="Paper counts" counts={paper?.status_counts} />
        </section>
        <section className="artifact-panel">
          <div className="section-label">Broker boundary</div>
          <h3>Submission health</h3>
          <dl className="metric-list compact">
            <MetricRow label="Latest submit" value={broker?.latest_submit_session_id || '-'} />
            <MetricRow label="Submit state" value={broker?.latest_submit_state || '-'} />
            <MetricRow label="Order state" value={broker?.latest_order_state || '-'} />
            <MetricRow label="Latest issue" value={broker?.latest_issue_code || '-'} />
          </dl>
          <OpsChipRow label="Broker counts" counts={broker?.status_counts} />
          <OpsChipRow label="Alert counts" counts={broker?.alert_counts} />
        </section>
      </div>

      {/* Launch + Stepbit */}
      <div className="artifact-grid">
        <section className="artifact-panel">
          <div className="section-label">Launch continuity</div>
          <h3>Recent launch job</h3>
          {latestJob ? (
            <dl className="metric-list compact">
              <MetricRow label="Request" value={latestJob.request_id || '-'} />
              <MetricRow label="Command" value={titleCase(latestJob.command || 'unknown')} />
              <MetricRow label="Launch state" value={launchSig.label} tone={launchSig.tone} />
              <MetricRow label="Run id" value={latestJob.run_id || '-'} />
            </dl>
          ) : (
            <div className="empty-state">
              No launch jobs are available yet. This is expected before the first launch request.
            </div>
          )}
        </section>
        <section className="artifact-panel">
          <div className="section-label">Stepbit boundary</div>
          <h3>Optional copiloted runtime</h3>
          <dl className="metric-list compact">
            <MetricRow label="Boundary note" value={stepbit?.boundary_note || '-'} />
            <MetricRow label="Frontend" value={liveUrls?.frontend_reachable ? 'reachable' : 'down'} />
            <MetricRow label="Backend" value={liveUrls?.backend_reachable ? 'reachable' : 'down'} />
            <MetricRow label="Core" value={liveUrls?.core_ready ? 'ready' : liveUrls?.core_reachable ? 'up' : 'down'} />
          </dl>
        </section>
      </div>
    </div>
  );
}
