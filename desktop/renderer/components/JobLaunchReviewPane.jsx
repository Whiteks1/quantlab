import React from 'react';
import { useQuantLab } from './QuantLabContext';
import {
  formatDateTime,
  formatLogPreview,
  titleCase,
} from '../modules/utils';

const MAX_LOG_PREVIEW_CHARS = 5000;

function resolveLaunchSignal(value) {
  const normalized = String(value || '').toLowerCase();
  if (!normalized || normalized === 'none') return { label: 'Launch pending', tone: 'tone-warning' };
  if (normalized.includes('succeeded')) return { label: 'Completed', tone: 'tone-positive' };
  if (normalized.includes('failed')) return { label: 'Failed', tone: 'tone-negative' };
  if (normalized.includes('running') || normalized.includes('queued') || normalized.includes('pending')) {
    return { label: 'In flight', tone: 'tone-warning' };
  }
  return { label: titleCase(value), tone: 'tone-warning' };
}

function buildFailureExplanation(job, stderrText) {
  if (!job) return 'No launch job information is available.';
  if (job.status !== 'failed') {
    return job.status === 'succeeded'
      ? 'This launch completed successfully. Use the run tab or artifacts tab for deeper inspection.'
      : 'This launch is still in progress, so a failure explanation is not available yet.';
  }

  const stderr = String(stderrText || job.error_message || '').trim();
  const lowered = stderr.toLowerCase();
  let likelyCause = 'QuantLab reported a generic runtime failure. Review stderr for the exact failing step.';

  if (lowered.includes('ticker') || lowered.includes('start') || lowered.includes('end')) {
    likelyCause = 'The failure looks related to missing or invalid launch parameters.';
  } else if (lowered.includes('config')) {
    likelyCause = 'The failure looks related to a missing or invalid sweep configuration file.';
  } else if (lowered.includes('import') || lowered.includes('module')) {
    likelyCause = 'The failure looks related to a Python environment or dependency import problem.';
  } else if (lowered.includes('permission') || lowered.includes('access is denied')) {
    likelyCause = 'The failure looks related to file-system permissions or path access.';
  } else if (lowered.includes('no such file') || lowered.includes('not found')) {
    likelyCause = 'The failure looks related to a missing file or artifact path.';
  }

  const lastLine = stderr.split(/\r?\n/).filter(Boolean).slice(-1)[0] || '';
  return [
    likelyCause,
    lastLine ? `Last stderr line: ${lastLine}` : '',
    job.error_message ? `Reported error: ${job.error_message}` : '',
  ].filter(Boolean).join(' ');
}

function SummaryCard({ label, value, tone = '' }) {
  return (
    <article className={`summary-card ${tone}`}>
      <div className="label">{label}</div>
      <div className={`value ${tone}`}>{value || '-'}</div>
    </article>
  );
}

export function JobLaunchReviewPane({ tab }) {
  const {
    findJob,
    openTab,
    refreshJobTab,
  } = useQuantLab();

  const requestId = tab.requestId || tab.jobId;
  const job = findJob(requestId) || tab.job;

  if (!job) {
    return (
      <div className="tab-shell artifact-shell tab-placeholder">
        The requested launch job is no longer present in the current snapshot.
      </div>
    );
  }

  if (tab.status === 'loading') {
    return (
      <div className="tab-shell artifact-shell tab-placeholder">
        Reading launch logs for {job.request_id || requestId || 'unknown'}...
      </div>
    );
  }

  if (tab.status === 'error') {
    return (
      <div className="tab-shell artifact-shell tab-placeholder">
        {tab.error || 'Could not load launch job details.'}
      </div>
    );
  }

  const statusSignal = resolveLaunchSignal(job.status);
  const failureSummary = buildFailureExplanation(job, tab.stderrText || '');
  const stdoutText = formatLogPreview(tab.stdoutText || 'No stdout captured.', MAX_LOG_PREVIEW_CHARS);
  const stderrText = formatLogPreview(tab.stderrText || job.error_message || 'No stderr captured.', MAX_LOG_PREVIEW_CHARS);

  const openExternal = (href) => {
    if (href && typeof window.quantlabDesktop?.openExternal === 'function') {
      window.quantlabDesktop.openExternal(href);
    }
  };

  const openArtifacts = () => {
    if (job.run_id) {
      openTab('artifacts', job.run_id);
      return;
    }
    openExternal(job.artifacts_href);
  };

  return (
    <div className="tab-shell artifact-shell job-launch-review-shell" data-job-review-shell="true">
      <div className="artifact-top">
        <div>
          <div className="section-label">Launch review</div>
          <h3>{job.request_id || requestId || 'unknown'}</h3>
          <div className="artifact-meta">
            {titleCase(job.command || 'unknown')} · {job.summary || '-'}
          </div>
        </div>
        <div className="workflow-actions">
          <button className="ghost-btn" type="button" onClick={() => refreshJobTab(requestId, job)}>
            Refresh logs
          </button>
          {job.run_id && (
            <button className="ghost-btn" type="button" onClick={() => openTab('run', job.run_id)}>
              Open run
            </button>
          )}
          {(job.run_id || job.artifacts_href) && (
            <button className="ghost-btn" type="button" onClick={openArtifacts}>
              Artifacts
            </button>
          )}
          {job.stderr_href && (
            <button className="ghost-btn" type="button" onClick={() => openExternal(job.stderr_href)}>
              Open stderr
            </button>
          )}
        </div>
      </div>

      <div className="tab-summary-grid">
        <SummaryCard label="Launch state" value={statusSignal.label} tone={statusSignal.tone} />
        <SummaryCard label="Started" value={formatDateTime(job.started_at)} />
        <SummaryCard label="Ended" value={formatDateTime(job.ended_at)} />
        <SummaryCard label="Run id" value={job.run_id || '-'} />
      </div>

      <section className="artifact-panel">
        <div className="section-label">Failure review</div>
        <h3>Deterministic summary</h3>
        <div className="artifact-meta">{failureSummary}</div>
      </section>

      <div className="artifact-grid">
        <section className="artifact-panel">
          <div className="section-label">Stdout</div>
          <h3>Process output</h3>
          <pre className="log-preview">{stdoutText}</pre>
        </section>
        <section className="artifact-panel">
          <div className="section-label">Stderr</div>
          <h3>Error output</h3>
          <pre className="log-preview">{stderrText}</pre>
        </section>
      </div>
    </div>
  );
}
