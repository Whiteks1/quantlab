import {
  buildRunArtifactHref,
  collectConfigDeltas,
  escapeHtml,
  formatBytes,
  formatCount,
  formatDateTime,
  formatLogPreview,
  formatMetricForDisplay,
  formatNumber,
  formatPercent,
  rankRunsByMetric,
  selectPrimaryResult,
  selectTopResults,
  shortCommit,
  summarizeObjectEntries,
  titleCase,
  toneClass,
} from "./utils.js";
import {
  renderActionButton,
  renderActionRow,
  renderEmptyState,
  renderMetricList,
} from "./view-primitives.js";

const TONE_ALIAS = {
  up: "tone-positive",
  down: "tone-negative",
  warn: "tone-warning",
  muted: "tone-neutral",
  positive: "tone-positive",
  negative: "tone-negative",
  warning: "tone-warning",
  neutral: "tone-neutral",
};

function normalizeTone(tone = "") {
  const normalized = String(tone || "").trim();
  return TONE_ALIAS[normalized] || normalized;
}

export function renderSummaryCard(label, value, tone = "") {
  const toneClass = normalizeTone(tone);
  return `<article class="summary-card ${escapeHtml(toneClass)}"><div class="label">${escapeHtml(label)}</div><div class="value ${escapeHtml(toneClass)}">${escapeHtml(value)}</div></article>`;
}

export function compareMetric(label, value, extraClass) {
  return `<div class="${escapeHtml(normalizeTone(extraClass))}"><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`;
}

function renderStateChip(label, value, tone = "") {
  const toneClass = normalizeTone(tone);
  return `<span class="run-state-chip ${escapeHtml(toneClass)}">${escapeHtml(label)} <strong>${escapeHtml(value)}</strong></span>`;
}

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

function resolveEvidenceSignal(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("ready") || normalized.includes("available") || normalized.includes("present")) {
    return { label: "Ready", tone: "tone-positive" };
  }
  if (normalized.includes("missing")) {
    return { label: "Missing", tone: "tone-warning" };
  }
  return { label: "Pending", tone: "tone-warning" };
}

function resolveBinarySignal(isReady, readyLabel, waitingLabel, options = {}) {
  return {
    label: isReady ? readyLabel : waitingLabel,
    tone: isReady ? (options.readyTone || "tone-positive") : (options.waitingTone || "tone-warning"),
  };
}

function resolveSnapshotSourceSignal(source) {
  if (source === "api") return { label: "API live", tone: "tone-positive" };
  if (source === "local") return { label: "Local fallback", tone: "tone-warning" };
  return { label: "Detached", tone: "tone-warning" };
}

function resolveWorkspaceBootstrapSignal(workspace) {
  if (workspace?.status === "ready") return { label: "Attached", tone: "tone-positive" };
  if (workspace?.status === "starting") return { label: "Booting", tone: "tone-warning" };
  if (workspace?.status === "error" || workspace?.status === "stopped") return { label: "Review required", tone: "tone-negative" };
  return { label: "Pending", tone: "tone-warning" };
}

export function renderCandidateFlags(store, runId, decision) {
  const labels = [];
  if (decision.isBaselineRun(store, runId)) labels.push('<span class="candidate-flag baseline">Baseline</span>');
  if (decision.isShortlistedRun(store, runId)) labels.push('<span class="candidate-flag shortlist">Shortlist</span>');
  if (decision.isCandidateRun(store, runId)) labels.push('<span class="candidate-flag candidate">Candidate</span>');
  return labels.length ? labels.join("") : '<span class="candidate-flag neutral">Untracked</span>';
}

export function renderCompactEntryList(entries) {
  return entries.length
    ? renderMetricList(entries.map(([label, value]) => ({ label, value })), { compact: true })
    : renderEmptyState("No structured config entries were available.");
}

export function renderLocalFilesList(entries, truncated = false) {
  if (!entries.length) {
    return renderEmptyState("No local files were discoverable in the run directory.");
  }
  return `
    <div class="artifact-list">
      ${entries.map((entry) => `
        <button class="artifact-link" type="button" data-open-path="${escapeHtml(entry.path)}">
          <span>${escapeHtml(entry.relative_path || entry.name)}</span>
          <span>${escapeHtml(entry.kind === "directory" ? "dir" : formatBytes(entry.size_bytes))}</span>
        </button>
      `).join("")}
    </div>
    ${truncated ? `<div class="artifact-meta">File listing truncated to the first visible entries.</div>` : ""}
  `;
}

export function renderCandidateCard(entry, forceShow, ctx) {
  if (!entry) return "";
  const { decision, findRun } = ctx;
  const run = entry.run || findRun(entry.run_id);
  const title = run?.run_id || entry.run_id;
  const metrics = run
    ? `
      <dl class="metric-list candidate-metric-list">
        ${compareMetric("Return", formatPercent(run.total_return), toneClass(run.total_return, true))}
        ${compareMetric("Sharpe", formatNumber(run.sharpe_simple), "")}
        ${compareMetric("Drawdown", formatPercent(run.max_drawdown), toneClass(run.max_drawdown, false))}
        ${compareMetric("Trades", formatCount(run.trades), "")}
        ${compareMetric("Commit", shortCommit(run.git_commit) || "-", "")}
        ${compareMetric("Window", `${run.start || "-"} -> ${run.end || "-"}`, "")}
      </dl>
    `
    : `<div class="empty-state">This run is no longer indexed, but the decision record is still preserved locally.</div>`;
  const noteText = entry.note ? escapeHtml(entry.note) : "No note yet.";
  return `
    <article class="candidate-card ${forceShow ? "baseline-card" : ""}">
      <div class="section-label">${forceShow ? "Pinned baseline" : entry.shortlisted ? "Shortlisted candidate" : "Tracked candidate"}</div>
      <div class="run-row-top">
        <div class="run-row-title">
          <strong>${escapeHtml(title)}</strong>
          <div class="run-row-meta">
            <span>${escapeHtml(run?.ticker || "-")}</span>
            <span>${escapeHtml(run?.mode ? titleCase(run.mode) : "unavailable")}</span>
            <span>${escapeHtml(run?.created_at ? formatDateTime(run.created_at) : "not indexed")}</span>
          </div>
        </div>
        <div class="run-row-flags">${renderCandidateFlags(ctx.store, entry.run_id, decision)}</div>
      </div>
      ${metrics}
      <div class="candidate-note">${noteText}</div>
      ${renderActionRow([
        run ? renderActionButton({ label: "Open run", dataset: { openRun: entry.run_id } }) : "",
        run ? renderActionButton({ label: "Artifacts", dataset: { openArtifacts: entry.run_id } }) : "",
        renderActionButton({ label: entry.note ? "Edit note" : "Add note", dataset: { editNote: entry.run_id } }),
        renderActionButton({ label: entry.shortlisted ? "Remove shortlist" : "Add shortlist", dataset: { shortlistRun: entry.run_id } }),
        renderActionButton({ label: decision.isBaselineRun(ctx.store, entry.run_id) ? "Clear baseline" : "Set baseline", dataset: { setBaseline: entry.run_id } }),
        renderActionButton({ label: "Remove candidate", dataset: { markCandidate: entry.run_id } }),
      ])}
    </article>
  `;
}

export function renderRunsTab(_tab, ctx) {
  const runs = ctx.getRuns();
  const latestRun = ctx.getLatestRun?.() || null;
  const latestJob = ctx.getJobs?.()[0] || null;
  const latestFailedJob = ctx.getLatestFailedJob?.() || null;
  const paper = ctx.snapshot?.paperHealth || null;
  const broker = ctx.snapshot?.brokerHealth || null;
  const candidateEntries = ctx.decision.getCandidateEntriesResolved(ctx.store, ctx.findRun);
  const shortlistCount = candidateEntries.filter((entry) => entry.shortlisted && entry.run).length;
  const selectedRuns = ctx.getSelectedRuns?.() || [];
  const compareReady = shortlistCount + (ctx.store?.baseline_run_id ? 1 : 0) >= 2;
  const baselineRun = ctx.store?.baseline_run_id ? ctx.findRun(ctx.store.baseline_run_id) : null;
  const spotlightRun = selectedRuns[0] || baselineRun || latestRun || null;
  const spotlightJob = spotlightRun ? ctx.getRunRelatedJobs?.(spotlightRun.run_id)?.[0] || null : null;
  const spotlightSweepEntries = spotlightRun ? ctx.getSweepDecisionEntriesForRun(spotlightRun.run_id) : [];
  return `
    <div class="tab-shell runs-tab">
      <div class="artifact-top">
        <div>
          <div class="section-label">Run explorer</div>
          <h3>Runs</h3>
          <div class="artifact-meta">Primary workstation for indexed runs, local evidence, shortlist state, and operational continuity.</div>
        </div>
        ${renderActionRow([
          renderActionButton({ label: "Open legacy view", dataset: { openRunsLegacy: true } }),
          renderActionButton({ label: "Open candidates", dataset: { openCandidates: true } }),
          renderActionButton({ label: "Open paper ops", dataset: { openOps: true } }),
        ])}
      </div>
      <div class="tab-summary-grid">
        ${renderSummaryCard("Indexed runs", formatCount(runs.length), runs.length ? "tone-positive" : "tone-warning")}
        ${renderSummaryCard("Candidates", formatCount(candidateEntries.length), candidateEntries.length ? "tone-warning" : "")}
        ${renderSummaryCard("Shortlisted", formatCount(shortlistCount), shortlistCount ? "tone-positive" : "")}
        ${renderSummaryCard("Baseline", ctx.store?.baseline_run_id || "Unset", ctx.store?.baseline_run_id ? "tone-positive" : "tone-warning")}
        ${renderSummaryCard("Launch state", resolveLaunchSignal(latestJob?.status, { emptyLabel: "Launch pending" }).label, resolveLaunchSignal(latestJob?.status, { emptyLabel: "Launch pending" }).tone)}
        ${renderSummaryCard("Paper state", paper?.available ? "Ready" : "Pending", paper?.available ? "tone-positive" : "tone-warning")}
      </div>
      <div class="runs-workbench">
        <div class="runs-workbench-main">
          ${renderRunsTable(runs, ctx)}
        </div>
        <aside class="runs-workbench-side">
          ${renderRunsSpotlightCard(ctx, spotlightRun, spotlightJob, spotlightSweepEntries, selectedRuns.length)}
          ${renderRunsDecisionQueueCard(ctx, candidateEntries, shortlistCount, compareReady, selectedRuns.length)}
          ${renderRunsOperationalCard(ctx, latestJob, latestFailedJob, paper, broker)}
        </aside>
      </div>
    </div>
  `;
}

function renderRunsSpotlightCard(ctx, spotlightRun, spotlightJob, spotlightSweepEntries, selectedCount) {
  const railLabel = selectedCount
    ? `Selected context · ${formatCount(selectedCount)} pinned`
    : ctx.store?.baseline_run_id
      ? "Pinned baseline"
      : "Latest indexed run";
  if (!spotlightRun) {
    return `
      <section class="artifact-panel run-spotlight-card run-rail-card evidence-rail-card">
        <div class="section-label">${escapeHtml(railLabel)}</div>
        <h3>No run indexed yet</h3>
        <div class="empty-state">Launch a run or wait for canonical artifacts to populate the registry.</div>
      </section>
    `;
  }
  const decisionSignal = resolveDecisionSignal(ctx.decision.summarizeCandidateState(ctx.store, spotlightRun.run_id));
  const launchSignal = resolveLaunchSignal(spotlightJob?.status, { emptyLabel: "Launch pending" });
  const evidenceSignal = resolveEvidenceSignal(spotlightRun.path ? "ready" : "missing");
  const sweepLabel = spotlightSweepEntries.length ? `${formatCount(spotlightSweepEntries.length)} tracked rows` : "None";
  return `
    <section class="artifact-panel run-spotlight-card run-rail-card evidence-rail-card">
      <div class="section-label">${escapeHtml(railLabel)}</div>
      <h3>${escapeHtml(spotlightRun.run_id)}</h3>
      <div class="artifact-meta">${escapeHtml(spotlightRun.ticker || "-")} · ${escapeHtml(titleCase(spotlightRun.mode || "unknown"))} · ${escapeHtml(formatDateTime(spotlightRun.created_at))}</div>
      <div class="run-row-flags">${renderCandidateFlags(ctx.store, spotlightRun.run_id, ctx.decision)}</div>
      <div class="run-row-metrics">
        <span class="metric-chip ${toneClass(spotlightRun.total_return, true)}">Return ${formatPercent(spotlightRun.total_return)}</span>
        <span class="metric-chip">Sharpe ${formatNumber(spotlightRun.sharpe_simple)}</span>
        <span class="metric-chip ${toneClass(spotlightRun.max_drawdown, false)}">Drawdown ${formatPercent(spotlightRun.max_drawdown)}</span>
        <span class="metric-chip">Trades ${formatCount(spotlightRun.trades)}</span>
      </div>
      ${renderRailPostureList([
        { label: "Decision state", value: decisionSignal.label, tone: decisionSignal.tone },
        { label: "Evidence state", value: evidenceSignal.label, tone: evidenceSignal.tone },
        { label: "Launch state", value: launchSignal.label, tone: launchSignal.tone },
        { label: "Sweep linkage", value: sweepLabel, tone: spotlightSweepEntries.length ? "tone-positive" : "tone-warning" },
        { label: "Window", value: `${spotlightRun.start || "-"} -> ${spotlightRun.end || "-"}` },
      ])}
      ${renderActionRow([
        renderActionButton({ label: "Open run", dataset: { openRun: spotlightRun.run_id } }),
        renderActionButton({ label: "Artifacts", dataset: { openArtifacts: spotlightRun.run_id } }),
        spotlightJob ? renderActionButton({ label: "Launch review", dataset: { openRelatedJob: spotlightRun.run_id } }) : "",
      ])}
    </section>
  `;
}

function renderRunsDecisionQueueCard(ctx, candidateEntries, shortlistCount, compareReady, selectedCount) {
  const baselineSignal = resolveBinarySignal(Boolean(ctx.store?.baseline_run_id), ctx.store?.baseline_run_id || "Pinned", "Unset");
  const compareSignal = resolveBinarySignal(compareReady, "Ready", "Incomplete");
  return `
    <section class="artifact-panel run-spotlight-card run-rail-card evidence-rail-card">
      <div class="section-label">Decision queue</div>
      <h3>Selection memory</h3>
      <div class="artifact-meta">Keep shortlist, baseline, and selected runs aligned before opening compare.</div>
      ${renderRailPostureList([
        { label: "Candidates", value: formatCount(candidateEntries.length), tone: candidateEntries.length ? "tone-warning" : "" },
        { label: "Shortlisted", value: formatCount(shortlistCount), tone: shortlistCount ? "tone-positive" : "" },
        { label: "Baseline", value: baselineSignal.label, tone: baselineSignal.tone },
        { label: "Selected set", value: formatCount(selectedCount), tone: selectedCount ? "tone-positive" : "" },
        { label: "Compare state", value: compareSignal.label, tone: compareSignal.tone },
      ], { compact: true })}
      ${renderActionRow([
        renderActionButton({ label: "Open queue", dataset: { openCandidates: true } }),
        renderActionButton({ label: "Shortlist compare", dataset: { openShortlistCompare: true }, disabled: !compareReady }),
      ])}
    </section>
  `;
}

function renderRunsOperationalCard(ctx, latestJob, latestFailedJob, paper, broker) {
  const launchSignal = resolveLaunchSignal(latestJob?.status, { emptyLabel: "Launch pending" });
  const sourceSignal = resolveSnapshotSourceSignal(ctx.snapshotStatus?.source);
  const brokerAlertCount = broker?.has_alerts ? (broker?.alerts || []).length : 0;
  return `
    <section class="artifact-panel run-spotlight-card run-rail-card evidence-rail-card">
      <div class="section-label">Operational context</div>
      <h3>Launch and runtime continuity</h3>
      <div class="artifact-meta">This rail stays useful even when the shell is running from local fallback data.</div>
      ${renderRailPostureList([
        { label: "Snapshot source", value: sourceSignal.label, tone: sourceSignal.tone },
        { label: "Latest launch", value: latestJob?.request_id || "none", tone: latestJob?.request_id ? "" : "tone-warning" },
        { label: "Launch state", value: launchSignal.label, tone: launchSignal.tone },
        { label: "Latest failed launch", value: latestFailedJob?.request_id || "none", tone: latestFailedJob ? "tone-warning" : "" },
        { label: "Paper state", value: paper?.available ? "Ready" : "Pending", tone: paper?.available ? "tone-positive" : "tone-warning" },
        { label: "Broker alerts", value: formatCount(brokerAlertCount), tone: brokerAlertCount ? "tone-negative" : "tone-positive" },
      ], { compact: true })}
      ${renderActionRow([
        latestJob?.request_id ? renderActionButton({ label: "Review latest launch", dataset: { openJob: latestJob.request_id } }) : "",
        renderActionButton({ label: "Paper ops", dataset: { openOps: true } }),
        renderActionButton({ label: "System", dataset: { openSystemTab: true } }),
      ])}
    </section>
  `;
}

export function renderRunTab(tab, ctx) {
  const run = ctx.findRun(tab.runId);
  if (!run) return `<div class="tab-placeholder">The requested run is no longer present in the registry.</div>`;
  if (tab.status === "loading") return `<div class="tab-placeholder">Reading canonical run detail for ${escapeHtml(run.run_id)}...</div>`;
  if (tab.status === "error") return `<div class="tab-placeholder">${escapeHtml(tab.error || "Could not load run detail.")}</div>`;

  const detail = tab.detail || {};
  const report = detail.report;
  const primaryResult = selectPrimaryResult(run, report);
  const configEntries = summarizeObjectEntries(report?.config_resolved);
  const fileEntries = detail.directoryEntries || [];
  const topResults = selectTopResults(report?.results, 4);
  const candidateEntry = ctx.decision.getCandidateEntry(ctx.store, run.run_id);
  const relatedJobs = ctx.getRunRelatedJobs(run.run_id);
  const latestRelatedJob = relatedJobs[0] || null;
  const sweepEntries = ctx.getSweepDecisionEntriesForRun(run.run_id);
  const decisionState = ctx.decision.summarizeCandidateState(ctx.store, run.run_id);
  const hasDecisionPeers = ctx.decision.isBaselineRun(ctx.store, run.run_id)
    ? ctx.decision.getCandidateEntriesResolved(ctx.store, ctx.findRun).length > 1
    : Boolean(ctx.store.baseline_run_id || ctx.decision.isShortlistedRun(ctx.store, run.run_id));
  const decisionNote = candidateEntry?.note ? escapeHtml(candidateEntry.note) : "No local decision note yet.";
  const relatedJobSignal = resolveLaunchSignal(latestRelatedJob?.status, { emptyLabel: "Launch pending" });
  const continuityState = latestRelatedJob
    ? `${relatedJobSignal.label} · ${formatDateTime(latestRelatedJob.created_at)}`
    : relatedJobSignal.label;
  const relatedJobTone = relatedJobSignal.tone;
  return `
    <div class="tab-shell run-detail-shell">
      ${renderRunIdentityHeader(run, ctx, latestRelatedJob, decisionState, continuityState)}
      ${renderRunMetricsSummary(run)}
      <div class="run-detail-grid">
        <div class="run-detail-main">
          <section class="artifact-panel">
            <div class="section-label">Result evidence</div>
            <h3>Decision metric snapshot</h3>
            <div class="run-evidence-stack">
              ${renderRunPrimaryResultBlock(primaryResult)}
              ${renderRunTopResultsBlock(topResults)}
            </div>
          </section>
          <section class="artifact-panel">
            <div class="section-label">Config and provenance</div>
            <h3>How this run was produced</h3>
            <div class="run-evidence-stack">
              ${renderRunConfigProvenanceBlock(run, report)}
              ${renderRunResolvedConfigBlock(configEntries)}
            </div>
          </section>
          <section class="artifact-panel">
            <div class="section-label">Linked evidence</div>
            <h3>Sweep and launch continuity</h3>
            <div class="run-evidence-stack">
              ${renderRunLaunchReviewBlock(run, latestRelatedJob, relatedJobTone)}
              ${renderRunSweepLinkageBlock(ctx, sweepEntries)}
            </div>
          </section>
        </div>
        <aside class="run-detail-side run-evidence-rail">
          ${renderRunDecisionBlock(run, ctx, candidateEntry, decisionNote, hasDecisionPeers)}
          ${renderRunArtifactsContinuityBlock(run, fileEntries, detail, latestRelatedJob, continuityState, sweepEntries)}
        </aside>
      </div>
    </div>
  `;
}

function renderRunIdentityHeader(run, ctx, latestRelatedJob, decisionState, continuityState) {
  const decisionSignal = resolveDecisionSignal(decisionState);
  const continuitySignal = resolveLaunchSignal(latestRelatedJob?.status, { emptyLabel: "Launch pending" });
  return `
    <div class="run-identity-header">
      <div class="run-identity-copy">
        <div class="section-label">Run workspace</div>
        <h2 class="run-identity-title">${escapeHtml(run.run_id)}</h2>
        <div class="run-identity-meta">
          <span>${escapeHtml(run.ticker || "-")}</span>
          <span>${escapeHtml(titleCase(run.mode || "unknown"))}</span>
          <span>${escapeHtml(formatDateTime(run.created_at))}</span>
          <span class="mono-cell">${escapeHtml(shortCommit(run.git_commit) || "-")}</span>
        </div>
        <div class="run-identity-state">
          ${renderStateChip("Decision", decisionSignal.label, decisionSignal.tone)}
          ${renderStateChip("Launch", continuityState, continuitySignal.tone)}
        </div>
      </div>
      <div class="run-identity-side">
        <div class="run-row-flags">${renderCandidateFlags(ctx.store, run.run_id, ctx.decision)}</div>
        <div class="workflow-actions">
          <button class="ghost-btn" type="button" data-open-browser-run="${escapeHtml(run.run_id)}">Browser view</button>
          <button class="ghost-btn" type="button" data-open-artifacts="${escapeHtml(run.run_id)}">Artifacts</button>
          <button class="ghost-btn" type="button" data-open-decision-compare="${escapeHtml(run.run_id)}">Decision compare</button>
          ${latestRelatedJob ? `<button class="ghost-btn" type="button" data-open-related-job="${escapeHtml(run.run_id)}">Latest launch review</button>` : ""}
        </div>
      </div>
    </div>
  `;
}

function renderRunMetricsSummary(run) {
  return `
    <div class="tab-summary-grid run-metrics-summary">
      ${renderSummaryCard("Return", formatPercent(run.total_return), toneClass(run.total_return, true))}
      ${renderSummaryCard("Sharpe", formatNumber(run.sharpe_simple))}
      ${renderSummaryCard("Drawdown", formatPercent(run.max_drawdown), toneClass(run.max_drawdown, false))}
      ${renderSummaryCard("Trades", formatCount(run.trades))}
    </div>
  `;
}

function renderRunDecisionBlock(run, ctx, candidateEntry, decisionNote, hasDecisionPeers) {
  const decisionSignal = resolveDecisionSignal(ctx.decision.summarizeCandidateState(ctx.store, run.run_id));
  return `
    <section class="artifact-panel run-rail-card">
      <div class="section-label">Decision / validation</div>
      <h3>What should happen next</h3>
      <div class="run-row-flags">${renderCandidateFlags(ctx.store, run.run_id, ctx.decision)}</div>
      <div class="artifact-meta">Decision state: <span class="${escapeHtml(decisionSignal.tone)}">${escapeHtml(decisionSignal.label)}</span></div>
      <div class="candidate-note">${decisionNote}</div>
      ${renderActionRow([
        renderActionButton({ label: ctx.decision.isCandidateRun(ctx.store, run.run_id) ? "Unmark candidate" : "Mark candidate", dataset: { markCandidate: run.run_id } }),
        renderActionButton({ label: ctx.decision.isShortlistedRun(ctx.store, run.run_id) ? "Remove shortlist" : "Add shortlist", dataset: { shortlistRun: run.run_id } }),
        renderActionButton({ label: ctx.decision.isBaselineRun(ctx.store, run.run_id) ? "Clear baseline" : "Set baseline", dataset: { setBaseline: run.run_id } }),
        renderActionButton({ label: candidateEntry?.note ? "Edit note" : "Add note", dataset: { editNote: run.run_id } }),
      ])}
      ${renderActionRow([
        renderActionButton({ label: "Compare with decision set", dataset: { openDecisionCompare: run.run_id }, disabled: !hasDecisionPeers }),
        renderActionButton({ label: "Open candidates", dataset: { openCandidates: true } }),
      ])}
      ${hasDecisionPeers ? `<div class="artifact-meta">This run can be compared directly against the current shortlist or baseline.</div>` : `<div class="artifact-meta">Pin a baseline or shortlist another run to enable decision compare from here.</div>`}
    </section>
  `;
}

function renderRunConfigProvenanceBlock(run, report) {
  return `
    <div class="nested-panel">
      <div class="section-label">Run provenance</div>
      <h3>Source and reproduction</h3>
      <dl class="metric-list compact">
        ${compareMetric("Mode", titleCase(run.mode || "unknown"), "")}
        ${compareMetric("Ticker", run.ticker || "-", "")}
        ${compareMetric("Window", `${run.start || "-"} -> ${run.end || "-"}`, "")}
        ${compareMetric("Commit", shortCommit(run.git_commit) || "-", "")}
        ${compareMetric("Path", run.path || "-", "")}
        ${compareMetric("Config path", report?.header?.config_path || "-", "")}
        ${compareMetric("Config hash", report?.header?.config_hash || "-", "")}
        ${compareMetric("Python", report?.header?.python_version || "-", "")}
        ${compareMetric("Reproduce", report?.reproduce?.command || "-", "")}
      </dl>
    </div>
  `;
}

function renderRunArtifactsContinuityBlock(run, fileEntries, detail, latestRelatedJob, continuityState, sweepEntries) {
  const hasCanonicalReport = Boolean(detail.report);
  const launchSignal = resolveLaunchSignal(latestRelatedJob?.status, { emptyLabel: "Launch pending" });
  const keyFileEntries = fileEntries.slice(0, 4);
  return `
    <section class="artifact-panel run-rail-card evidence-rail-card">
      <div class="section-label">Evidence rail</div>
      <h3>Artifacts and operational links</h3>
      <div class="artifact-meta">Validate report availability, local files, launch continuity, and sweep linkage without leaving the run.</div>
      ${renderRailPostureList([
        { label: "Report state", value: hasCanonicalReport ? "Ready" : "Missing", tone: hasCanonicalReport ? "tone-positive" : "tone-warning" },
        { label: "Workspace files", value: fileEntries.length ? `${formatCount(fileEntries.length)} files` : "Pending", tone: fileEntries.length ? "tone-positive" : "tone-warning" },
        { label: "Launch continuity", value: continuityState, tone: launchSignal.tone },
        { label: "Launch state", value: launchSignal.label, tone: launchSignal.tone },
        { label: "Sweep linkage", value: sweepEntries.length ? `${formatCount(sweepEntries.length)} tracked rows` : "None", tone: sweepEntries.length ? "tone-positive" : "tone-warning" },
        { label: "Workspace path", value: run.path || "-" },
      ], { compact: true })}
      ${keyFileEntries.length ? `
        <div class="run-rail-section">
          <div class="section-label">Key files</div>
          <div class="run-rail-file-strip">
            ${keyFileEntries.map((entry) => `
              <button class="run-rail-file-chip" type="button" data-open-path="${escapeHtml(entry.path)}">
                <span>${escapeHtml(entry.relative_path || entry.name)}</span>
                <span>${escapeHtml(entry.kind === "directory" ? "dir" : formatBytes(entry.size_bytes))}</span>
              </button>
            `).join("")}
          </div>
        </div>
      ` : ""}
      ${renderActionRow([
        renderActionButton({ label: "Inspect artifacts", dataset: { openArtifacts: run.run_id } }),
        renderActionButton({ label: "Browser view", dataset: { openBrowserRun: run.run_id } }),
        latestRelatedJob ? renderActionButton({ label: "Latest launch review", dataset: { openRelatedJob: run.run_id } }) : "",
        latestRelatedJob?.stderr_href ? renderActionButton({ label: "Open stderr in browser", dataset: { openJobLink: latestRelatedJob.stderr_href } }) : "",
      ])}
      <div class="run-rail-section">
      <div class="section-label">Workspace files</div>
      <h3>Local artifact directory</h3>
      ${renderLocalFilesList(fileEntries.slice(0, 8), detail.directoryTruncated)}
      </div>
    </section>
  `;
}

function renderRailPostureList(entries, options = {}) {
  const items = entries.filter((entry) => entry && entry.label);
  if (!items.length) return "";
  return `
    <div class="rail-posture-list ${options.compact ? "compact" : ""}">
      ${items.map((entry) => renderRailPostureRow(entry.label, entry.value, entry.tone || "")).join("")}
    </div>
  `;
}

function renderRailPostureRow(label, value, tone = "") {
  return `
    <div class="rail-posture-row">
      <div class="rail-posture-copy">
        <div class="rail-posture-label">${escapeHtml(label)}</div>
        <div class="rail-posture-value ${escapeHtml(tone)}">${escapeHtml(value)}</div>
      </div>
      <span class="rail-tone-dot ${escapeHtml(tone)}" aria-hidden="true"></span>
    </div>
  `;
}

function renderRunPrimaryResultBlock(primaryResult) {
  return `
    <div class="nested-panel">
      <div class="section-label">Primary result</div>
      <h3>${escapeHtml(primaryResult ? "Decision metric snapshot" : "No structured result available")}</h3>
      ${primaryResult ? `
        <dl class="metric-list">
          ${compareMetric("Return", formatPercent(primaryResult.total_return), toneClass(primaryResult.total_return, true))}
          ${compareMetric("Sharpe", formatNumber(primaryResult.sharpe_simple), "")}
          ${compareMetric("Drawdown", formatPercent(primaryResult.max_drawdown), toneClass(primaryResult.max_drawdown, false))}
          ${compareMetric("Trades", formatCount(primaryResult.trades), "")}
          ${compareMetric("Win rate", formatPercent(primaryResult.win_rate_trades), "")}
          ${compareMetric("Exposure", formatPercent(primaryResult.exposure), "")}
        </dl>
      ` : `<div class="empty-state">The canonical report did not expose a structured primary result for this run.</div>`}
    </div>
  `;
}

function renderRunResolvedConfigBlock(configEntries) {
  return `
    <div class="nested-panel">
      <div class="section-label">Resolved config</div>
      <h3>Effective parameters</h3>
      ${configEntries.length ? `
        <dl class="metric-list compact">
          ${configEntries.map(([label, value]) => compareMetric(label, value, "")).join("")}
        </dl>
      ` : `<div class="empty-state">No resolved config was available in the canonical report.</div>`}
    </div>
  `;
}

function renderRunLaunchReviewBlock(run, latestRelatedJob, relatedJobTone) {
  return `
    <div class="nested-panel">
      <div class="section-label">Launch review</div>
      <h3>${escapeHtml(latestRelatedJob ? `Latest job ${latestRelatedJob.request_id}` : "No linked launch job")}</h3>
      ${latestRelatedJob ? `
        <dl class="metric-list compact">
          ${compareMetric("Status", titleCase(latestRelatedJob.status || "unknown"), relatedJobTone)}
          ${compareMetric("Created", formatDateTime(latestRelatedJob.created_at), "")}
          ${compareMetric("Command", latestRelatedJob.command || "-", "")}
          ${compareMetric("Request", latestRelatedJob.request_id || "-", "")}
        </dl>
        ${renderActionRow([
          renderActionButton({ label: "Open launch review", dataset: { openRelatedJob: run.run_id } }),
          latestRelatedJob.stderr_href ? renderActionButton({ label: "Open stderr in browser", dataset: { openJobLink: latestRelatedJob.stderr_href } }) : "",
        ])}
      ` : renderEmptyState("This run does not currently expose a launch job in the local launch registry.")}
    </div>
  `;
}

function renderRunTopResultsBlock(topResults) {
  return `
    <div class="nested-panel">
      <div class="section-label">Top result rows</div>
      <h3>Best rows from report.json</h3>
      ${topResults.length ? `
        <div class="mini-table">
          <div class="mini-table-row head">
            <span>Return</span>
            <span>Sharpe</span>
            <span>Drawdown</span>
            <span>Trades</span>
          </div>
          ${topResults.map((result) => `
            <div class="mini-table-row">
              <span class="${escapeHtml(toneClass(result.total_return, true))}">${escapeHtml(formatPercent(result.total_return))}</span>
              <span>${escapeHtml(formatNumber(result.sharpe_simple))}</span>
              <span class="${escapeHtml(toneClass(result.max_drawdown, false))}">${escapeHtml(formatPercent(result.max_drawdown))}</span>
              <span>${escapeHtml(formatCount(result.trades))}</span>
            </div>
          `).join("")}
        </div>
      ` : `<div class="empty-state">This run did not expose comparable result rows.</div>`}
    </div>
  `;
}

function renderRunSweepLinkageBlock(ctx, sweepEntries) {
  return `
    <div class="nested-panel">
      <div class="section-label">Sweep linkage</div>
      <h3>${escapeHtml(sweepEntries.length ? "Tracked sweep rows for this run" : "No sweep handoff rows")}</h3>
      ${sweepEntries.length ? `
        <div class="mini-table">
          <div class="mini-table-row head">
            <span>Entry</span>
            <span>State</span>
            <span>Sharpe</span>
            <span>Return</span>
          </div>
          ${sweepEntries.slice(0, 4).map((entry) => `
            <div class="mini-table-row">
              <span>${escapeHtml(entry.entry_id)}</span>
              <span>${escapeHtml(ctx.sweepDecision.summarizeState(ctx.sweepDecisionStore, entry.entry_id))}</span>
              <span>${escapeHtml(formatNumber(entry.row?.sharpe_simple ?? entry.row_snapshot?.sharpe_simple))}</span>
              <span>${escapeHtml(formatPercent(entry.row?.total_return ?? entry.row_snapshot?.total_return))}</span>
            </div>
          `).join("")}
        </div>
        <div class="workflow-actions">
          <button class="ghost-btn" type="button" data-open-sweep-handoff="tracked">Open sweep handoff</button>
        </div>
      ` : `<div class="empty-state">This run is not currently represented in the local sweep handoff store.</div>`}
    </div>
  `;
}
export function renderCompareTab(tab, ctx) {
  const runs = (tab.runIds || []).map(ctx.findRun).filter(Boolean);
  if (runs.length < 2) {
    return `<div class="tab-placeholder">The selected compare set is no longer available in the registry.</div>`;
  }
  if (tab.status === "loading") {
    return `<div class="tab-placeholder">Preparing decision-oriented compare for ${runs.length} runs...</div>`;
  }
  const rankMetric = tab.rankMetric || "sharpe_simple";
  const rankedRuns = rankRunsByMetric(runs, rankMetric);
  const winner = rankedRuns[0];
  const runnerUp = rankedRuns[1] || null;
  const detailMap = tab.detailMap || {};
  const configDeltaEntries = collectConfigDeltas(runs, detailMap);
  const includedBaseline = runs.find((run) => ctx.decision.isBaselineRun(ctx.store, run.run_id)) || null;
  const shortlistedRuns = runs.filter((run) => ctx.decision.isShortlistedRun(ctx.store, run.run_id));
  const candidateRuns = runs.filter((run) => ctx.decision.isCandidateRun(ctx.store, run.run_id));
  return `
    <div class="compare-shell compare-tab">
      <div class="tab-summary-grid">
        ${renderSummaryCard("Compared runs", String(runs.length))}
        ${renderSummaryCard("Ranking metric", titleCase(rankMetric.replace("_", " ")))}
        ${renderSummaryCard("Winner", `${winner.run_id} · ${formatMetricForDisplay(winner[rankMetric], rankMetric)}`, rankMetric === "max_drawdown" ? toneClass(winner.max_drawdown, false) : toneClass(winner[rankMetric], true))}
        ${renderSummaryCard("Runner-up", runnerUp ? `${runnerUp.run_id} · ${formatMetricForDisplay(runnerUp[rankMetric], rankMetric)}` : "-")}
        ${renderSummaryCard("Baseline in set", includedBaseline ? includedBaseline.run_id : "No")}
        ${renderSummaryCard("Shortlisted in set", String(shortlistedRuns.length))}
      </div>
      <div class="compare-workbench">
        <div class="compare-workbench-main">
          <section class="artifact-panel">
            <div class="section-label">Ranking matrix</div>
            <h3>Decision-ready compare set</h3>
            <div class="artifact-meta">Rank, inspect, and promote runs without leaving the compare surface.</div>
            ${renderCompareRankingTable(rankedRuns, rankMetric, ctx)}
          </section>
          <section class="artifact-panel">
            <div class="section-label">Config deltas</div>
            <h3>What changes across this compare set</h3>
            ${configDeltaEntries.length ? `
              <div class="mini-table">
                <div class="mini-table-row head">
                  <span>Key</span>
                  <span>Values</span>
                </div>
                ${configDeltaEntries.map(([key, values]) => `
                  <div class="mini-table-row">
                    <span>${escapeHtml(key)}</span>
                    <span>${escapeHtml(values.join(" | "))}</span>
                  </div>
                `).join("")}
              </div>
            ` : `<div class="empty-state">No resolved config deltas were available yet for this compare set.</div>`}
          </section>
        </div>
        <aside class="compare-workbench-side">
          <section class="artifact-panel run-spotlight-card compare-winner-card">
            <div class="section-label">Current leader</div>
            <h3>${escapeHtml(winner.run_id)}</h3>
            <div class="artifact-meta">${escapeHtml(winner.ticker || "-")} · ${escapeHtml(titleCase(winner.mode || "unknown"))} · ranked by ${escapeHtml(titleCase(rankMetric.replace("_", " ")))}</div>
            <dl class="metric-list compact">
              ${compareMetric("Rank metric", formatMetricForDisplay(winner[rankMetric], rankMetric), rankMetric === "max_drawdown" ? toneClass(winner.max_drawdown, false) : toneClass(winner[rankMetric], true))}
              ${compareMetric("Return", formatPercent(winner.total_return), toneClass(winner.total_return, true))}
              ${compareMetric("Sharpe", formatNumber(winner.sharpe_simple), "")}
              ${compareMetric("Drawdown", formatPercent(winner.max_drawdown), toneClass(winner.max_drawdown, false))}
              ${compareMetric("Trades", formatCount(winner.trades), "")}
            </dl>
            <div class="run-row-flags">${renderCandidateFlags(ctx.store, winner.run_id, ctx.decision)}</div>
            <div class="workflow-actions">
              <button class="ghost-btn" type="button" data-open-run="${escapeHtml(winner.run_id)}">Open winner</button>
              <button class="ghost-btn" type="button" data-open-artifacts="${escapeHtml(winner.run_id)}">Winner artifacts</button>
              <button class="ghost-btn" type="button" data-mark-candidate="${escapeHtml(winner.run_id)}">${ctx.decision.isCandidateRun(ctx.store, winner.run_id) ? "Unmark candidate" : "Mark candidate"}</button>
              <button class="ghost-btn" type="button" data-shortlist-run="${escapeHtml(winner.run_id)}">${ctx.decision.isShortlistedRun(ctx.store, winner.run_id) ? "Remove shortlist" : "Add shortlist"}</button>
              <button class="ghost-btn" type="button" data-set-baseline="${escapeHtml(winner.run_id)}">${ctx.decision.isBaselineRun(ctx.store, winner.run_id) ? "Clear baseline" : "Set baseline"}</button>
            </div>
          </section>
          <section class="artifact-panel run-spotlight-card">
            <div class="section-label">Ranking controls</div>
            <h3>Re-rank compare set</h3>
            <div class="workflow-actions compare-rank-actions">
              ${["sharpe_simple", "total_return", "max_drawdown", "trades"].map((metric) => `
                <button class="ghost-btn ${rankMetric === metric ? "is-selected" : ""}" type="button" data-compare-rank="${escapeHtml(metric)}">${escapeHtml(titleCase(metric.replace("_", " ")))}</button>
              `).join("")}
            </div>
            <dl class="metric-list compact">
              ${compareMetric("Candidates in set", formatCount(candidateRuns.length), candidateRuns.length ? "tone-warning" : "")}
              ${compareMetric("Shortlisted in set", formatCount(shortlistedRuns.length), shortlistedRuns.length ? "tone-positive" : "")}
              ${compareMetric("Baseline present", includedBaseline ? "yes" : "no", includedBaseline ? "tone-positive" : "tone-warning")}
              ${compareMetric("Runner-up", runnerUp?.run_id || "none", "")}
            </dl>
          </section>
        </aside>
      </div>
    </div>
  `;
}

function renderRunsTable(runs, ctx) {
  if (!Array.isArray(runs) || !runs.length) {
    return renderEmptyState("No runs are indexed yet. Launch a run or wait for canonical artifacts to appear.");
  }
  return `
    <div class="runs-table-wrap">
      <table class="runs-table">
        <thead>
          <tr>
            <th>Run</th>
            <th>Hypothesis / Window</th>
            <th>Return</th>
            <th>Sharpe</th>
            <th>Drawdown</th>
            <th>State</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${runs.map((run) => renderRunsRow(run, ctx)).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderRunsRow(run, ctx) {
  const runId = run?.run_id || "";
  const commitLabel = shortCommit(run?.git_commit) || "-";
  const decision = ctx.decision;
  const store = ctx.store;
  const candidateLabel = decision.isCandidateRun(store, runId) ? "Unmark candidate" : "Mark candidate";
  const latestJob = ctx.getRunRelatedJobs?.(runId)?.[0] || null;
  const decisionSignal = resolveDecisionSignal(decision.summarizeCandidateState(store, runId));
  const launchSignal = resolveLaunchSignal(latestJob?.status, { emptyLabel: "Launch pending" });
  const evidenceSignal = resolveEvidenceSignal(run?.path ? "available" : "missing");
  return `
    <tr class="runs-row">
      <td>
        <div class="run-primary-cell">
          <div class="run-primary-title-row">
            <span class="mono-cell run-primary-id">${escapeHtml(runId)}</span>
            <span class="run-inline-chip">${escapeHtml(titleCase(run?.mode || "unknown"))}</span>
          </div>
          <div class="run-primary-meta">
            <span>${escapeHtml(run?.ticker || "-")}</span>
            <span>${escapeHtml(formatDateTime(run?.created_at))}</span>
            <span class="mono-cell">${escapeHtml(commitLabel)}</span>
          </div>
          <div class="run-flags-cell" style="margin-top:6px;">${renderCandidateFlags(store, runId, decision)}</div>
        </div>
      </td>
      <td>
        <div style="display: flex; flex-direction: column; gap: 4px; white-space: nowrap;">
          <span class="mono-cell">${escapeHtml(`${run?.start || "-"} -> ${run?.end || "-"}`)}</span>
          <span style="color: var(--muted); font-size: 0.76rem;">Trades: ${escapeHtml(formatCount(run?.trades))}</span>
        </div>
      </td>
      <td class="${escapeHtml(toneClass(run?.total_return, true))}">${escapeHtml(formatPercent(run?.total_return))}</td>
      <td>${escapeHtml(formatNumber(run?.sharpe_simple))}</td>
      <td class="${escapeHtml(toneClass(run?.max_drawdown, false))}">${escapeHtml(formatPercent(run?.max_drawdown))}</td>
      <td>
        <div class="run-state-stack">
          ${renderRunsStateRow("Decision", decisionSignal.label, decisionSignal.tone)}
          ${renderRunsStateRow("Launch", launchSignal.label, launchSignal.tone)}
          ${renderRunsStateRow("Evidence", evidenceSignal.label, evidenceSignal.tone)}
        </div>
      </td>
      <td>
        <div class="runs-row-actions">
          ${renderActionButton({ label: "Inspect", dataset: { openRun: runId } })}
          ${renderActionButton({ label: "Artifacts", dataset: { openArtifacts: runId } })}
          ${renderActionButton({ label: "Compare", dataset: { openDecisionCompare: runId } })}
          ${renderActionButton({ label: candidateLabel, dataset: { markCandidate: runId } })}
        </div>
      </td>
    </tr>
  `;
}

function renderRunsStateRow(label, value, tone) {
  const toneClass = normalizeTone(tone);
  return `
    <div class="run-state-row">
      <span class="run-state-dot ${escapeHtml(toneClass)}" aria-hidden="true"></span>
      <span class="run-state-label">${escapeHtml(label)}</span>
      <span class="run-state-value">${escapeHtml(value)}</span>
    </div>
  `;
}

function resolveRunsStateTone(value, kind) {
  if (kind === "decision") return resolveDecisionSignal(value).tone;
  if (kind === "launch") return resolveLaunchSignal(value, { emptyLabel: "Launch pending" }).tone;
  if (kind === "evidence") return resolveEvidenceSignal(value).tone;
  return "tone-neutral";
}

export function renderArtifactsTab(tab, ctx) {
  const run = ctx.findRun(tab.runId);
  if (!run) return `<div class="tab-placeholder">The requested run is no longer present in the registry.</div>`;
  if (tab.status === "loading") return `<div class="tab-placeholder">Reading canonical artifacts for ${escapeHtml(run.run_id)}...</div>`;
  if (tab.status === "error") return `<div class="tab-placeholder">${escapeHtml(tab.error || "Could not load artifact metadata.")}</div>`;
  const detail = tab.detail || { report: null, reportUrl: null, directoryEntries: [] };
  const report = detail.report;
  const artifacts = Array.isArray(report?.artifacts) ? report.artifacts : [];
  const primaryResult = selectPrimaryResult(run, report);
  const latestRelatedJob = ctx.getRunRelatedJobs(run.run_id)[0] || null;
  const configEntries = summarizeObjectEntries(report?.config_resolved);
  return `
    <div class="artifact-shell evidence-shell">
      <div class="artifact-top">
        <div>
          <div class="section-label">Artifacts</div>
          <h3>${escapeHtml(run.run_id)}</h3>
          <div class="artifact-meta">${escapeHtml(run.ticker || "-")} · ${escapeHtml(titleCase(run.mode || "unknown"))} · ${escapeHtml(formatDateTime(run.created_at))}</div>
        </div>
        ${renderActionRow([
          renderActionButton({ label: "Open run", dataset: { openRun: run.run_id } }),
          renderActionButton({ label: ctx.decision.isCandidateRun(ctx.store, run.run_id) ? "Unmark candidate" : "Mark candidate", dataset: { markCandidate: run.run_id } }),
          renderActionButton({ label: ctx.decision.isShortlistedRun(ctx.store, run.run_id) ? "Remove shortlist" : "Add shortlist", dataset: { shortlistRun: run.run_id } }),
          renderActionButton({ label: ctx.decision.isBaselineRun(ctx.store, run.run_id) ? "Clear baseline" : "Set baseline", dataset: { setBaseline: run.run_id } }),
          detail.reportUrl ? renderActionButton({ label: "Raw report", dataset: { openExternal: detail.reportUrl } }) : "",
        ])}
      </div>
      <div class="tab-summary-grid">
        ${renderSummaryCard("Manifest files", String(artifacts.length))}
        ${renderSummaryCard("Workspace files", String(detail.directoryEntries?.length || 0))}
        ${renderSummaryCard("Primary return", primaryResult ? formatPercent(primaryResult.total_return) : "-", primaryResult ? toneClass(primaryResult.total_return, true) : "")}
        ${renderSummaryCard("Primary sharpe", primaryResult ? formatNumber(primaryResult.sharpe_simple) : "-")}
      </div>
      <div class="evidence-grid">
        <div class="evidence-main">
          <section class="artifact-panel">
            <div class="section-label">Canonical outputs</div>
            <h3>Artifact manifest</h3>
            <div class="artifact-meta">Machine-readable files exposed by the canonical report for this run.</div>
            ${artifacts.length ? `<div class="artifact-list">
              ${artifacts.map((artifact) => {
                const href = buildRunArtifactHref(run.path, artifact.file_name);
                return `<button class="artifact-link" type="button" data-open-external="${escapeHtml(href)}"><span>${escapeHtml(artifact.file_name)}</span><span>${escapeHtml(formatBytes(artifact.size_bytes))}</span></button>`;
              }).join("")}
            </div>` : `<div class="empty-state">The canonical report does not expose an artifact manifest for this run.</div>`}
          </section>
          <section class="artifact-panel">
            <div class="section-label">Key outputs</div>
            <h3>Primary result and resolved context</h3>
            <div class="artifact-grid">
              <section class="artifact-panel nested-panel">
                <div class="section-label">Primary result</div>
                <h3>${escapeHtml(primaryResult ? "Decision metric snapshot" : "No structured result available")}</h3>
                ${primaryResult ? `
                  <dl class="metric-list">
                    ${compareMetric("Return", formatPercent(primaryResult.total_return), toneClass(primaryResult.total_return, true))}
                    ${compareMetric("Sharpe", formatNumber(primaryResult.sharpe_simple), "")}
                    ${compareMetric("Drawdown", formatPercent(primaryResult.max_drawdown), toneClass(primaryResult.max_drawdown, false))}
                    ${compareMetric("Trades", formatCount(primaryResult.trades), "")}
                  </dl>
                ` : `<div class="empty-state">The canonical report did not expose a structured primary result for this run.</div>`}
              </section>
              <section class="artifact-panel nested-panel">
                <div class="section-label">Resolved config</div>
                <h3>Effective parameters</h3>
                ${renderCompactEntryList(configEntries)}
              </section>
            </div>
          </section>
        </div>
        <div class="evidence-side">
          <section class="artifact-panel">
            <div class="section-label">Evidence continuity</div>
            <h3>Run outputs and links</h3>
            <dl class="metric-list compact">
              ${compareMetric("Window", `${run.start || "-"} -> ${run.end || "-"}`, "")}
              ${compareMetric("Output path", run.path || "-", "")}
              ${compareMetric("Raw report", detail.reportUrl ? "Available" : "Missing", "")}
              ${compareMetric("Launch review", latestRelatedJob?.request_id || "None", "")}
            </dl>
            <div class="workflow-actions">
              ${detail.reportUrl ? `<button class="ghost-btn" type="button" data-open-external="${escapeHtml(detail.reportUrl)}">Open report.json</button>` : ""}
              ${latestRelatedJob?.stderr_href ? `<button class="ghost-btn" type="button" data-open-external="${escapeHtml(latestRelatedJob.stderr_href)}">Open stderr</button>` : ""}
            </div>
          </section>
          <section class="artifact-panel">
            <div class="section-label">Local files</div>
            <h3>Workspace directory</h3>
            ${renderLocalFilesList(detail.directoryEntries || [], detail.directoryTruncated)}
          </section>
        </div>
      </div>
    </div>
  `;
}

export function renderCandidatesTab(tab, ctx) {
  const filter = tab.filter || "all";
  const allEntries = ctx.decision.getCandidateEntriesResolved(ctx.store, ctx.findRun);
  const sortedEntries = [...allEntries].sort((left, right) => {
    const leftBaseline = ctx.decision.isBaselineRun(ctx.store, left.run_id) ? 1 : 0;
    const rightBaseline = ctx.decision.isBaselineRun(ctx.store, right.run_id) ? 1 : 0;
    if (leftBaseline !== rightBaseline) return rightBaseline - leftBaseline;
    const leftShortlist = left.shortlisted ? 1 : 0;
    const rightShortlist = right.shortlisted ? 1 : 0;
    if (leftShortlist !== rightShortlist) return rightShortlist - leftShortlist;
    const leftCreated = new Date(left.run?.created_at || 0).getTime();
    const rightCreated = new Date(right.run?.created_at || 0).getTime();
    return rightCreated - leftCreated;
  });
  const shortlistEntries = sortedEntries.filter((entry) => entry.shortlisted);
  const visibleEntries = filter === "shortlist"
    ? shortlistEntries
    : filter === "baseline"
    ? sortedEntries.filter((entry) => entry.run_id === ctx.store.baseline_run_id)
    : sortedEntries;
  const compareReady = shortlistEntries.length + (ctx.store.baseline_run_id ? 1 : 0) >= 2;
  const visibleLabels = visibleEntries.slice(0, 4).map((entry) => entry.run_id);

  return `
    <div class="tab-shell candidates-tab">
      <div class="artifact-top">
        <div>
          <div class="section-label">Decision layer</div>
          <h3>Candidates and shortlist</h3>
          <div class="artifact-meta">Persisted locally in QuantLab Desktop. This is the minimum layer that turns observation into choice.</div>
        </div>
        ${renderActionRow([
          renderActionButton({ label: "Open shortlist compare", dataset: { openShortlistCompare: true } }),
          ctx.store.baseline_run_id ? renderActionButton({ label: "Open baseline", dataset: { openRun: ctx.store.baseline_run_id } }) : "",
        ])}
      </div>
      <div class="tab-summary-grid">
        ${renderSummaryCard("Candidates", String(sortedEntries.length))}
        ${renderSummaryCard("Shortlisted", String(shortlistEntries.length))}
        ${renderSummaryCard("Baseline", ctx.store.baseline_run_id || "None")}
        ${renderSummaryCard("Indexed runs", String(ctx.getRuns().length))}
      </div>
      <div class="candidates-workbench">
        <div class="candidates-workbench-main">
          <section class="artifact-panel">
            <div class="section-label">${escapeHtml(titleCase(filter))}</div>
            <h3>Decision queue</h3>
            <div class="artifact-meta">Sorted by baseline, shortlist, and recency so the queue behaves like a real operator surface.</div>
            ${visibleEntries.length ? `<div class="candidate-list">${visibleEntries.map((entry) => renderCandidateCard(entry, false, ctx)).join("")}</div>` : `<div class="empty-state">No runs match this candidate filter yet.</div>`}
          </section>
        </div>
        <aside class="candidates-workbench-side">
          <section class="artifact-panel run-spotlight-card">
            <div class="section-label">Queue controls</div>
            <h3>Focus the decision queue</h3>
            <div class="workflow-actions compare-rank-actions">
              ${["all", "shortlist", "baseline"].map((option) =>
                renderActionButton({
                  label: titleCase(option),
                  dataset: { candidatesFilter: option },
                  className: `ghost-btn ${filter === option ? "is-selected" : ""}`.trim(),
                }),
              ).join("")}
            </div>
            ${renderMetricList([
              { label: "Visible entries", value: formatCount(visibleEntries.length) },
              { label: "Compare ready", value: compareReady ? "yes" : "no", tone: compareReady ? "tone-positive" : "tone-warning" },
              { label: "Visible run ids", value: visibleLabels.length ? visibleLabels.join(", ") : "none" },
            ], { compact: true })}
            ${renderActionRow([
              renderActionButton({ label: "Open shortlist compare", dataset: { openShortlistCompare: true }, disabled: !compareReady }),
            ])}
          </section>
          ${ctx.store.baseline_run_id ? `
            <section class="artifact-panel run-spotlight-card">
              <div class="section-label">Pinned reference</div>
              <h3>Baseline</h3>
              ${renderCandidateCard(
                ctx.decision.getCandidateEntryResolved(ctx.store, ctx.store.baseline_run_id, ctx.findRun) ||
                  ctx.decision.buildMissingCandidateEntry(ctx.store.baseline_run_id, ctx.findRun),
                true,
                ctx,
              )}
            </section>
          ` : `
            <section class="artifact-panel run-spotlight-card">
              <div class="section-label">Pinned reference</div>
              <h3>No baseline yet</h3>
              <div class="empty-state">Pin one run as baseline so compare stays anchored while the shortlist evolves.</div>
            </section>
          `}
          <section class="artifact-panel run-spotlight-card">
            <div class="section-label">Shortlist state</div>
            <h3>Comparison readiness</h3>
            ${shortlistEntries.length ? `
              <div class="artifact-list compact-artifact-list">
                ${shortlistEntries.slice(0, 4).map((entry) => `
                  <button class="artifact-link compact-link" type="button" data-open-run="${escapeHtml(entry.run_id)}">
                    <span>${escapeHtml(entry.run_id)}</span>
                    <span>${escapeHtml(entry.run?.ticker || "-")}</span>
                  </button>
                `).join("")}
              </div>
            ` : `<div class="empty-state">No shortlisted runs yet. Promote candidates here before opening compare.</div>`}
          </section>
        </aside>
      </div>
    </div>
  `;
}

function renderCompareRankingTable(runs, rankMetric, ctx) {
  return `
    <div class="runs-table-wrap compare-table-wrap">
      <table class="runs-table compare-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Run</th>
            <th>Mode</th>
            <th>Ticker</th>
            <th>Created</th>
            <th>Rank metric</th>
            <th>Return</th>
            <th>Sharpe</th>
            <th>Drawdown</th>
            <th>Trades</th>
            <th>Flags</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${runs.map((run, index) => `
            <tr class="runs-row compare-row ${index === 0 ? "compare-row-leader" : ""}">
              <td class="mono-cell">#${index + 1}</td>
              <td class="mono-cell">${escapeHtml(run.run_id)}</td>
              <td>${escapeHtml(titleCase(run.mode || "unknown"))}</td>
              <td>${escapeHtml(run.ticker || "-")}</td>
              <td>${escapeHtml(formatDateTime(run.created_at))}</td>
              <td class="${escapeHtml(rankMetric === "max_drawdown" ? toneClass(run.max_drawdown, false) : toneClass(run[rankMetric], true))}">${escapeHtml(formatMetricForDisplay(run[rankMetric], rankMetric))}</td>
              <td class="${escapeHtml(toneClass(run.total_return, true))}">${escapeHtml(formatPercent(run.total_return))}</td>
              <td>${escapeHtml(formatNumber(run.sharpe_simple))}</td>
              <td class="${escapeHtml(toneClass(run.max_drawdown, false))}">${escapeHtml(formatPercent(run.max_drawdown))}</td>
              <td>${escapeHtml(formatCount(run.trades))}</td>
              <td><div class="run-flags-cell">${renderCandidateFlags(ctx.store, run.run_id, ctx.decision)}</div></td>
              <td>
                <div class="runs-row-actions">
                  <button class="ghost-btn" type="button" data-open-run="${escapeHtml(run.run_id)}">Open</button>
                  <button class="ghost-btn" type="button" data-open-artifacts="${escapeHtml(run.run_id)}">Artifacts</button>
                  <button class="ghost-btn" type="button" data-shortlist-run="${escapeHtml(run.run_id)}">${ctx.decision.isShortlistedRun(ctx.store, run.run_id) ? "Unshortlist" : "Shortlist"}</button>
                  <button class="ghost-btn" type="button" data-set-baseline="${escapeHtml(run.run_id)}">${ctx.decision.isBaselineRun(ctx.store, run.run_id) ? "Clear baseline" : "Baseline"}</button>
                </div>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

export function renderExperimentsTab(tab, ctx) {
  const workspace = ctx.experimentsWorkspace || { status: "idle", configs: [], sweeps: [], error: null };
  const configs = Array.isArray(workspace.configs) ? workspace.configs : [];
  const sweeps = Array.isArray(workspace.sweeps) ? workspace.sweeps : [];
  const selectedConfig = configs.find((entry) => entry.path === tab.selectedConfigPath) || configs[0] || null;
  const selectedSweep = sweeps.find((entry) => entry.run_id === tab.selectedSweepId) || sweeps[0] || null;
  const latestSweep = sweeps[0] || null;
  const sweepDecisionEntries = ctx.sweepDecision.getEntriesResolved(ctx.sweepDecisionStore, ctx.findSweepDecisionRow);
  const sweepShortlistEntries = sweepDecisionEntries.filter((entry) => entry.shortlisted);
  const sweepBaselineEntry = sweepDecisionEntries.find((entry) => entry.entry_id === ctx.sweepDecisionStore?.baseline_entry_id) || null;

  if (workspace.status === "loading" && !configs.length && !sweeps.length) {
    return `<div class="tab-placeholder">Reading experiment configs and recent sweep artifacts from the local workspace...</div>`;
  }

  if (workspace.status === "error" && !configs.length && !sweeps.length) {
    return `<div class="tab-placeholder">${escapeHtml(workspace.error || "Could not read local experiment workspace.")}</div>`;
  }

  const selectedSweepFiles = selectedSweep?.files || [];
  const fileByName = (fileName) => selectedSweepFiles.find((entry) => entry.name === fileName) || null;
  const selectedSweepResultRows = selectedSweep?.topResults?.length
    ? selectedSweep.topResults
    : selectedSweep?.leaderboardRows || [];

  return `
    <div class="tab-shell">
      <div class="artifact-top">
        <div>
          <div class="section-label">Experiment workspace</div>
          <h3>Configs and recent sweeps</h3>
          <div class="artifact-meta">Local-first shell surface for launching sweeps, inspecting their outputs, and resuming quantitative iteration without leaving QuantLab Desktop.</div>
        </div>
        <div class="workflow-actions">
          <button class="ghost-btn" type="button" data-experiments-refresh="true">Refresh</button>
          ${selectedConfig ? `<button class="ghost-btn" type="button" data-experiment-launch-config="${escapeHtml(selectedConfig.path)}">Launch selected config</button>` : ""}
          ${selectedSweep ? `<button class="ghost-btn" type="button" data-experiment-open-path="${escapeHtml(selectedSweep.path)}">Open sweep folder</button>` : ""}
        </div>
      </div>
      <div class="tab-summary-grid">
        ${renderSummaryCard("Configs", String(configs.length))}
        ${renderSummaryCard("Recent sweeps", String(sweeps.length))}
        ${renderSummaryCard("Latest mode", latestSweep ? titleCase(latestSweep.mode || "unknown") : "None")}
        ${renderSummaryCard("Latest sweep", latestSweep?.run_id || "None")}
        ${renderSummaryCard("Tracked sweep rows", String(sweepDecisionEntries.length))}
        ${renderSummaryCard("Sweep shortlist", String(sweepShortlistEntries.length))}
      </div>
      <div class="artifact-grid experiments-grid">
        <section class="artifact-panel">
          <div class="section-label">Catalog</div>
          <h3>Experiment configs</h3>
          ${configs.length ? `
            <div class="candidate-list">
              ${configs.map((config) => `
                <article class="candidate-card ${selectedConfig?.path === config.path ? "is-selected" : ""}">
                  <div class="run-row-top">
                    <div class="run-row-title">
                      <strong>${escapeHtml(config.name)}</strong>
                      <div class="run-row-meta">
                        <span>${escapeHtml(config.relativePath)}</span>
                        <span>${escapeHtml(formatDateTime(config.modifiedAt))}</span>
                        <span>${escapeHtml(formatBytes(config.sizeBytes))}</span>
                      </div>
                    </div>
                  </div>
                  <div class="workflow-actions">
                    <button class="ghost-btn" type="button" data-experiment-config="${escapeHtml(config.path)}">${selectedConfig?.path === config.path ? "Selected" : "Preview"}</button>
                    <button class="ghost-btn" type="button" data-experiment-launch-config="${escapeHtml(config.path)}">Launch sweep</button>
                    <button class="ghost-btn" type="button" data-experiment-open-file="${escapeHtml(config.path)}">Open file</button>
                  </div>
                </article>
              `).join("")}
            </div>
          ` : `<div class="empty-state">No experiment configs were found under configs/experiments.</div>`}
        </section>
        <section class="artifact-panel">
          <div class="section-label">Preview</div>
          <h3>${escapeHtml(selectedConfig?.name || "Select a config")}</h3>
          ${selectedConfig?.previewText
            ? `<pre class="log-preview config-preview">${escapeHtml(selectedConfig.previewText)}</pre>`
            : `<div class="empty-state">Choose an experiment config to preview its YAML and launch a sweep from the shell.</div>`}
        </section>
      </div>
      <div class="artifact-grid experiments-grid">
        <section class="artifact-panel">
          <div class="section-label">Recent outputs</div>
          <h3>Sweeps</h3>
          ${sweeps.length ? `
            <div class="candidate-list">
              ${sweeps.map((sweep) => `
                <article class="candidate-card ${selectedSweep?.run_id === sweep.run_id ? "is-selected" : ""}">
                  <div class="run-row-top">
                    <div class="run-row-title">
                      <strong>${escapeHtml(sweep.run_id)}</strong>
                      <div class="run-row-meta">
                        <span>${escapeHtml(titleCase(sweep.mode || "unknown"))}</span>
                        <span>${escapeHtml(sweep.configName || sweep.configPath || "-")}</span>
                        <span>${escapeHtml(formatDateTime(sweep.createdAt))}</span>
                      </div>
                    </div>
                    <span class="mode-chip">${escapeHtml(titleCase(sweep.mode || "sweep"))}</span>
                  </div>
                  <div class="run-row-metrics">
                    <span class="metric-chip ${toneClass(sweep.headlineReturn, true)}">Return ${formatPercent(sweep.headlineReturn)}</span>
                    <span class="metric-chip">Sharpe ${formatNumber(sweep.headlineSharpe)}</span>
                    <span class="metric-chip ${toneClass(sweep.headlineDrawdown, false)}">Drawdown ${formatPercent(sweep.headlineDrawdown)}</span>
                    <span class="metric-chip">Runs ${formatCount(sweep.nRuns)}</span>
                  </div>
                  <div class="workflow-actions">
                    <button class="ghost-btn" type="button" data-experiment-sweep="${escapeHtml(sweep.run_id)}">${selectedSweep?.run_id === sweep.run_id ? "Selected" : "Open details"}</button>
                    ${sweep.configPath ? `<button class="ghost-btn" type="button" data-experiment-relaunch="${escapeHtml(sweep.configPath)}">Launch again</button>` : ""}
                    <button class="ghost-btn" type="button" data-experiment-open-path="${escapeHtml(sweep.path)}">Folder</button>
                  </div>
                </article>
              `).join("")}
            </div>
          ` : `<div class="empty-state">No sweep output directories were found yet under outputs/sweeps.</div>`}
        </section>
        <section class="artifact-panel">
          <div class="section-label">Selected sweep</div>
          <h3>${escapeHtml(selectedSweep?.run_id || "Choose a sweep")}</h3>
          ${selectedSweep ? `
            <div class="tab-summary-grid">
              ${renderSummaryCard("Mode", titleCase(selectedSweep.mode || "unknown"))}
              ${renderSummaryCard("Config", selectedSweep.configName || "Unknown")}
              ${renderSummaryCard("Sweep runs", formatCount(selectedSweep.nRuns))}
              ${renderSummaryCard("Selected test rows", formatCount(selectedSweep.nSelected))}
              ${renderSummaryCard("Train runs", formatCount(selectedSweep.nTrainRuns))}
              ${renderSummaryCard("Test runs", formatCount(selectedSweep.nTestRuns))}
            </div>
            <div class="workflow-actions">
              <button class="ghost-btn" type="button" data-experiment-open-path="${escapeHtml(selectedSweep.path)}">Open folder</button>
              ${fileByName("meta.json") ? `<button class="ghost-btn" type="button" data-experiment-open-file="${escapeHtml(fileByName("meta.json").path)}">meta.json</button>` : ""}
              ${fileByName("leaderboard.csv") ? `<button class="ghost-btn" type="button" data-experiment-open-file="${escapeHtml(fileByName("leaderboard.csv").path)}">leaderboard.csv</button>` : ""}
              ${fileByName("experiments.csv") ? `<button class="ghost-btn" type="button" data-experiment-open-file="${escapeHtml(fileByName("experiments.csv").path)}">experiments.csv</button>` : ""}
              ${fileByName("config_resolved.yaml") ? `<button class="ghost-btn" type="button" data-experiment-open-file="${escapeHtml(fileByName("config_resolved.yaml").path)}">config_resolved.yaml</button>` : ""}
              <button class="ghost-btn" type="button" data-open-sweep-handoff="tracked">Open sweep handoff</button>
            </div>
            <div class="artifact-grid">
              <section class="artifact-panel">
                <div class="section-label">Top rows</div>
                <h3>Leaderboard snapshot</h3>
                ${selectedSweepResultRows.length ? `
                  <div class="mini-table">
                    <div class="mini-table-row head">
                      <span>Return</span>
                      <span>Sharpe</span>
                      <span>Drawdown</span>
                      <span>Trades</span>
                    </div>
                    ${selectedSweepResultRows.map((row) => `
                      <div class="mini-table-row">
                        <span class="${escapeHtml(toneClass(Number(row.total_return), true))}">${escapeHtml(formatPercent(Number(row.total_return)))}</span>
                        <span>${escapeHtml(formatNumber(Number(row.sharpe_simple ?? row.best_test_sharpe)))}</span>
                        <span class="${escapeHtml(toneClass(Number(row.max_drawdown), false))}">${escapeHtml(formatPercent(Number(row.max_drawdown)))}</span>
                        <span>${escapeHtml(formatCount(Number(row.trades ?? row.n_test_runs)))}</span>
                      </div>
                    `).join("")}
                  </div>
                ` : `<div class="empty-state">No leaderboard rows were readable for this sweep.</div>`}
              </section>
              <section class="artifact-panel">
                <div class="section-label">Walkforward summary</div>
                <h3>Selection and OOS</h3>
                ${selectedSweep.walkforwardRows?.length ? `
                  <div class="mini-table">
                    <div class="mini-table-row head">
                      <span>Split</span>
                      <span>Best test sharpe</span>
                      <span>Best test return</span>
                      <span>Selected</span>
                    </div>
                    ${selectedSweep.walkforwardRows.map((row) => `
                      <div class="mini-table-row">
                        <span>${escapeHtml(row.split_name || "-")}</span>
                        <span>${escapeHtml(formatNumber(Number(row.best_test_sharpe)))}</span>
                        <span>${escapeHtml(formatPercent(Number(row.best_test_return)))}</span>
                        <span>${escapeHtml(formatCount(Number(row.n_selected)))}</span>
                      </div>
                    `).join("")}
                  </div>
                ` : `<div class="empty-state">This sweep did not expose walkforward summary rows.</div>`}
              </section>
            </div>
            <section class="artifact-panel">
              <div class="section-label">Decision handoff</div>
              <h3>Track top sweep rows</h3>
              <div class="tab-summary-grid">
                ${renderSummaryCard("Tracked", String(sweepDecisionEntries.length))}
                ${renderSummaryCard("Shortlisted", String(sweepShortlistEntries.length))}
                ${renderSummaryCard("Baseline", sweepBaselineEntry?.entry_id || "None")}
              </div>
              ${selectedSweep.decisionRows?.length ? `
                <div class="candidate-list">
                  ${selectedSweep.decisionRows.map((row) => renderSweepDecisionCard(row, ctx)).join("")}
                </div>
              ` : `<div class="empty-state">This sweep did not expose comparable leaderboard rows for handoff.</div>`}
            </section>
            <section class="artifact-panel">
              <div class="section-label">Workspace files</div>
              <h3>Local sweep directory</h3>
              ${renderLocalFilesList(selectedSweepFiles.slice(0, 12), selectedSweep.filesTruncated)}
            </section>
          ` : `<div class="empty-state">Select a recent sweep to inspect its local outputs.</div>`}
        </section>
      </div>
      <section class="artifact-panel">
        <div class="section-label">Tracked handoff</div>
        <h3>Sweep shortlist and baseline</h3>
        <div class="workflow-actions">
          <button class="ghost-btn" type="button" data-open-sweep-handoff="tracked">Open sweep handoff</button>
        </div>
        ${sweepDecisionEntries.length ? `<div class="candidate-list">${sweepDecisionEntries.map((entry) => renderSweepDecisionCard(entry, ctx)).join("")}</div>` : `<div class="empty-state">No sweep rows are tracked yet. Track a top row from the selected sweep to start the handoff layer.</div>`}
      </section>
    </div>
  `;
}

export function renderSweepDecisionTab(tab, ctx) {
  const rankMetric = tab.rankMetric || "sharpe_simple";
  const entries = ctx.getSweepDecisionCompareEntries();
  if (entries.length < 2) {
    return `<div class="tab-placeholder">Sweep handoff needs at least two tracked rows in shortlist or baseline before it can compare them.</div>`;
  }

  const rankedEntries = [...entries].sort((left, right) => {
    const leftRow = left.row || {};
    const rightRow = right.row || {};
    const leftValue = Number(leftRow[rankMetric] ?? Number.NEGATIVE_INFINITY);
    const rightValue = Number(rightRow[rankMetric] ?? Number.NEGATIVE_INFINITY);
    return rightValue - leftValue;
  });
  const winner = rankedEntries[0];
  const baseline = rankedEntries.find((entry) => ctx.sweepDecision.isBaseline(ctx.sweepDecisionStore, entry.entry_id)) || null;

  return `
    <div class="tab-shell">
      <div class="artifact-top">
        <div>
          <div class="section-label">Sweep handoff</div>
          <h3>Decision compare</h3>
          <div class="artifact-meta">Local decision surface for tracked sweep rows. This is intentionally lighter than the run compare surface.</div>
        </div>
        <div class="workflow-actions compare-rank-actions">
          ${["sharpe_simple", "total_return", "max_drawdown", "trades"].map((metric) => `
            <button class="ghost-btn ${rankMetric === metric ? "is-selected" : ""}" type="button" data-sweep-rank="${escapeHtml(metric)}">${escapeHtml(titleCase(metric.replace("_", " ")))}</button>
          `).join("")}
        </div>
      </div>
      <div class="tab-summary-grid">
        ${renderSummaryCard("Compared rows", String(rankedEntries.length))}
        ${renderSummaryCard("Ranking metric", titleCase(rankMetric.replace("_", " ")))}
        ${renderSummaryCard("Winner", `${winner.entry_id} · ${formatMetricForDisplay(winner.row?.[rankMetric], rankMetric)}`, toneClass(Number(winner.row?.[rankMetric]), rankMetric !== "max_drawdown"))}
        ${renderSummaryCard("Baseline", baseline?.entry_id || "None")}
      </div>
      <section class="artifact-panel">
        <div class="section-label">Tracked rows</div>
        <h3>Compare and decide</h3>
        <div class="candidate-list">
          ${rankedEntries.map((entry) => renderSweepDecisionCard(entry, ctx)).join("")}
        </div>
      </section>
    </div>
  `;
}

function renderSweepDecisionFlags(store, decision, entryId) {
  const labels = [];
  if (decision.isBaseline(store, entryId)) labels.push('<span class="candidate-flag baseline">Baseline</span>');
  if (decision.isShortlisted(store, entryId)) labels.push('<span class="candidate-flag shortlist">Shortlist</span>');
  if (decision.isTracked(store, entryId)) labels.push('<span class="candidate-flag candidate">Tracked</span>');
  return labels.length ? labels.join("") : '<span class="candidate-flag neutral">Untracked</span>';
}

function renderSweepDecisionCard(entry, ctx) {
  const storedEntry = ctx.sweepDecision.getEntry(ctx.sweepDecisionStore, entry.entry_id);
  const row = entry.row || entry.row_snapshot || entry;
  const sweepRunId = entry.sweep_run_id || row.sweep_run_id || row.sweep?.run_id || "-";
  const sweep = row.sweep || ctx.findSweep(sweepRunId) || null;
  const configPath = entry.config_path || row.config_path || sweep?.configPath || "";
  const note = storedEntry?.note || entry.note || "";
  return `
    <article class="candidate-card">
      <div class="run-row-top">
        <div class="run-row-title">
          <strong>${escapeHtml(entry.entry_id)}</strong>
          <div class="run-row-meta">
            <span>${escapeHtml(sweepRunId)}</span>
            <span>${escapeHtml(sweep?.configName || configPath || "-")}</span>
            <span>${escapeHtml(entry.label || row.label || `Row #${(entry.row_index ?? 0) + 1}`)}</span>
          </div>
        </div>
        <div class="run-row-flags">${renderSweepDecisionFlags(ctx.sweepDecisionStore, ctx.sweepDecision, entry.entry_id)}</div>
      </div>
      <div class="run-row-metrics">
        <span class="metric-chip ${toneClass(Number(row.total_return), true)}">Return ${formatPercent(Number(row.total_return))}</span>
        <span class="metric-chip">Sharpe ${formatNumber(Number(row.sharpe_simple ?? row.best_test_sharpe))}</span>
        <span class="metric-chip ${toneClass(Number(row.max_drawdown), false)}">Drawdown ${formatPercent(Number(row.max_drawdown))}</span>
        <span class="metric-chip">Trades ${formatCount(Number(row.trades ?? row.n_test_runs))}</span>
      </div>
      ${note ? `<div class="candidate-note">${escapeHtml(note)}</div>` : ""}
      ${renderActionRow([
        renderActionButton({ label: ctx.sweepDecision.isTracked(ctx.sweepDecisionStore, entry.entry_id) ? "Untrack" : "Track", dataset: { sweepTrackEntry: entry.entry_id } }),
        renderActionButton({ label: ctx.sweepDecision.isShortlisted(ctx.sweepDecisionStore, entry.entry_id) ? "Remove shortlist" : "Add shortlist", dataset: { sweepShortlistEntry: entry.entry_id } }),
        renderActionButton({ label: ctx.sweepDecision.isBaseline(ctx.sweepDecisionStore, entry.entry_id) ? "Clear baseline" : "Set baseline", dataset: { sweepBaselineEntry: entry.entry_id } }),
        renderActionButton({ label: note ? "Edit note" : "Add note", dataset: { sweepNoteEntry: entry.entry_id } }),
        configPath ? renderActionButton({ label: "Launch sweep", dataset: { experimentLaunchConfig: configPath } }) : "",
        sweep?.path ? renderActionButton({ label: "Open folder", dataset: { experimentOpenPath: sweep.path } }) : "",
      ])}
    </article>
  `;
}

export function renderSystemTab(ctx) {
  const workspace = ctx.workspace || {};
  const snapshotStatus = ctx.snapshotStatus || {};
  const snapshot = ctx.snapshot || {};
  const launchControl = snapshot.launchControl || null;
  const paper = snapshot.paperHealth || null;
  const broker = snapshot.brokerHealth || null;
  const stepbit = snapshot.stepbitWorkspace || null;
  const liveUrls = stepbit?.live_urls || {};
  const runs = ctx.getRuns?.() || [];
  const jobs = Array.isArray(launchControl?.jobs) ? launchControl.jobs.slice(0, 5) : [];
  const latestRun = ctx.getLatestRun?.() || null;
  const latestFailedJob = ctx.getLatestFailedJob?.() || null;
  const candidateEntries = ctx.decision.getCandidateEntriesResolved(ctx.store, ctx.findRun);
  const shortlistCount = candidateEntries.filter((entry) => entry.shortlisted && entry.run).length;
  const brokerAlerts = Array.isArray(broker?.alerts) ? broker.alerts : [];
  const systemUrls = collectSystemUrls(workspace, liveUrls);
  const logPreview = collectSystemLogPreview(workspace.logs, ctx.maxLogPreviewChars);
  const refreshState = describeSnapshotRefresh(snapshotStatus);
  const watchItems = buildSystemWatchItems({
    workspace,
    snapshotStatus,
    brokerAlerts,
    latestFailedJob,
    launchJobs: jobs,
    liveUrls,
    latestRun,
  });

  return `
    <div class="tab-shell">
      <div class="artifact-top">
        <div>
          <div class="section-label">Runtime diagnostics</div>
          <h3>System</h3>
          <div class="artifact-meta">Native runtime inventory for bootstrap state, API refresh, launch visibility, and workspace continuity.</div>
        </div>
        ${renderActionRow([
          renderActionButton({ label: "Retry runtime", dataset: { systemRetry: true } }),
          workspace.serverUrl ? renderActionButton({ label: "Open research_ui", dataset: { openSystemUrl: "/research_ui/index.html" } }) : "",
          latestRun?.run_id ? renderActionButton({ label: "Latest run", dataset: { openRun: latestRun.run_id } }) : "",
          jobs[0]?.request_id ? renderActionButton({ label: "Latest launch review", dataset: { openJob: jobs[0].request_id } }) : "",
        ])}
      </div>
      <div class="tab-summary-grid">
        ${renderSummaryCard("QuantLab", resolveWorkspaceBootstrapSignal(workspace).label, resolveWorkspaceBootstrapSignal(workspace).tone)}
        ${renderSummaryCard("Snapshot", refreshState.label, refreshState.tone)}
        ${renderSummaryCard("Indexed runs", formatCount(runs.length), runs.length ? "tone-positive" : "tone-warning")}
        ${renderSummaryCard("Launch jobs", formatCount(Array.isArray(launchControl?.jobs) ? launchControl.jobs.length : 0), jobs.length ? "tone-positive" : "tone-warning")}
        ${renderSummaryCard("Paper state", paper?.available ? "Ready" : "Pending", paper?.available ? "tone-positive" : "tone-warning")}
        ${renderSummaryCard("Broker alerts", formatCount(brokerAlerts.length), brokerAlerts.length ? "tone-negative" : broker?.available ? "tone-positive" : "tone-warning")}
        ${renderSummaryCard("Stepbit frontend", liveUrls.frontend_reachable ? "Attached" : "Detached", liveUrls.frontend_reachable ? "tone-positive" : "tone-warning")}
        ${renderSummaryCard("Stepbit core", liveUrls.core_ready ? "Ready" : liveUrls.core_reachable ? "Partial" : "Detached", liveUrls.core_ready ? "tone-positive" : liveUrls.core_reachable ? "tone-warning" : "tone-negative")}
      </div>
      <div class="artifact-grid system-grid">
        <section class="artifact-panel system-stack">
          <div class="section-label">Workspace</div>
          <h3>Bootstrap and refresh state</h3>
          <dl class="metric-list compact">
            ${compareMetric("Workspace state", resolveWorkspaceBootstrapSignal(workspace).label, resolveWorkspaceBootstrapSignal(workspace).tone)}
            ${compareMetric("Server URL", workspace.serverUrl || "pending", "")}
            ${compareMetric("Server source", titleCase(workspace.source || "unknown"), "")}
            ${compareMetric("Refresh state", refreshState.label, refreshState.tone)}
            ${compareMetric("Last refresh", refreshState.lastSuccessAt, "")}
            ${compareMetric("Consecutive refresh errors", formatCount(Number(snapshotStatus.consecutiveErrors || 0)), "")}
            ${compareMetric("Refresh mode", snapshotStatus.refreshPaused ? "Paused" : "Active", snapshotStatus.refreshPaused ? "tone-warning" : "tone-positive")}
            ${compareMetric("Workspace logs", formatCount(Array.isArray(workspace.logs) ? workspace.logs.length : 0), "")}
          </dl>
          ${workspace.error ? `<div class="ops-callout tone-negative">${escapeHtml(workspace.error)}</div>` : ""}
        </section>
        <section class="artifact-panel system-stack">
          <div class="section-label">Surfaces</div>
          <h3>Reachable local interfaces</h3>
          ${systemUrls.length ? `
            <div class="system-link-list">
              ${systemUrls.map((entry) => `
                <button class="system-link-item" type="button" data-open-system-url="${escapeHtml(entry.url)}">
                  <strong>${escapeHtml(entry.label)}</strong>
                  <span>${escapeHtml(entry.url)}</span>
                </button>
              `).join("")}
            </div>
          ` : `<div class="empty-state">No addressable local surfaces are visible yet. Wait for bootstrap or retry the runtime.</div>`}
        </section>
        <section class="artifact-panel system-stack">
          <div class="section-label">Launch queue</div>
          <h3>Recent tracked jobs</h3>
          ${jobs.length ? `
            <div class="system-job-list">
              ${jobs.map((job) => `
                <button class="system-job-item" type="button" data-open-job="${escapeHtml(job.request_id || "")}">
                  <div class="system-job-top">
                    <strong>${escapeHtml(titleCase(job.command || "unknown"))}</strong>
                    <span class="${escapeHtml(resolveLaunchSignal(job.status, { emptyLabel: "Launch pending" }).tone)}">${escapeHtml(resolveLaunchSignal(job.status, { emptyLabel: "Launch pending" }).label)}</span>
                  </div>
                  <div class="artifact-meta">${escapeHtml(job.request_id || "-")}${job.run_id ? ` · ${escapeHtml(job.run_id)}` : ""}</div>
                  <div class="artifact-meta">${escapeHtml(job.summary || "No summary")} · ${escapeHtml(formatDateTime(job.created_at || job.started_at))}</div>
                </button>
              `).join("")}
            </div>
          ` : `<div class="empty-state">No launch jobs are available yet.</div>`}
        </section>
        <section class="artifact-panel system-stack">
          <div class="section-label">Decision memory</div>
          <h3>Local selection state</h3>
          <dl class="metric-list compact">
            ${compareMetric("Candidates", formatCount(candidateEntries.length), "")}
            ${compareMetric("Shortlisted", formatCount(shortlistCount), "")}
            ${compareMetric("Baseline", ctx.store?.baseline_run_id || "none", "")}
            ${compareMetric("Latest run", latestRun?.run_id || "none", "")}
            ${compareMetric("Latest failed launch", latestFailedJob?.request_id || "none", "")}
          </dl>
        </section>
      </div>
      <div class="artifact-grid system-grid">
        <section class="artifact-panel system-stack">
          <div class="section-label">Attention</div>
          <h3>What needs operator review</h3>
          <div class="system-watch-list">
            ${watchItems.map((item) => `
              <article class="system-watch-item tone-${escapeHtml(item.tone || "neutral")}">
                <strong>${escapeHtml(item.label)}</strong>
                <p>${escapeHtml(item.body)}</p>
              </article>
            `).join("")}
          </div>
        </section>
        <section class="artifact-panel system-stack">
          <div class="section-label">Workspace logs</div>
          <h3>Latest bootstrap output</h3>
          ${logPreview ? `<pre class="system-log">${escapeHtml(logPreview)}</pre>` : `<div class="empty-state">No workspace log lines have been captured yet.</div>`}
        </section>
      </div>
    </div>
  `;
}

export function renderPaperOpsTab(ctx) {
  const paper = ctx.snapshot?.paperHealth || null;
  const broker = ctx.snapshot?.brokerHealth || null;
  const stepbit = ctx.snapshot?.stepbitWorkspace || null;
  const latestJob = ctx.getJobs()[0] || null;
  const latestFailedJob = ctx.getLatestFailedJob?.() || null;
  const latestRun = ctx.getLatestRun?.() || null;
  const decisionCompareRunIds = ctx.getDecisionCompareRunIds?.() || [];
  const candidateEntries = ctx.decision.getCandidateEntriesResolved(ctx.store, ctx.findRun);
  const shortlistCount = candidateEntries.filter((entry) => entry.shortlisted && entry.run).length;
  const baselineRunId = ctx.store?.baseline_run_id || "";
  const paperReady = Boolean(paper?.available && paper?.total_sessions);
  const brokerReady = Boolean(broker?.available);
  const brokerHasAlerts = Boolean(broker?.has_alerts);
  const stepbitLive = Boolean(stepbit?.live_urls?.frontend_reachable && stepbit?.live_urls?.backend_reachable);

  const nowItems = [
    {
      tone: paperReady ? "positive" : "warning",
      label: "Paper track",
      title: paperReady ? `${paper.total_sessions} sessions tracked` : "No paper sessions tracked yet",
      meta: paper?.latest_session_status
        ? `Latest status ${titleCase(paper.latest_session_status)}${paper?.latest_session_at ? ` · ${formatDateTime(paper.latest_session_at)}` : ""}`
        : "Paper execution has not produced visible sessions yet.",
    },
    {
      tone: brokerHasAlerts ? "negative" : brokerReady ? "positive" : "warning",
      label: "Broker boundary",
      title: brokerHasAlerts ? "Broker alerts require review" : brokerReady ? "Broker validations are visible" : "Broker validations not present yet",
      meta: brokerHasAlerts
        ? `${formatCount((broker?.alerts || []).length)} active alerts across the submission boundary.`
        : brokerReady
          ? `${formatCount(broker?.total_sessions || 0)} broker validation sessions indexed.`
          : broker?.message || "No broker order-validation surface is indexed yet.",
    },
    {
      tone: decisionCompareRunIds.length >= 2 ? "positive" : candidateEntries.length ? "warning" : "",
      label: "Decision queue",
      title: decisionCompareRunIds.length >= 2 ? `${decisionCompareRunIds.length} runs ready to compare` : candidateEntries.length ? "Decision memory is partial" : "No decision queue yet",
      meta: `Candidates ${formatCount(candidateEntries.length)} · Shortlist ${formatCount(shortlistCount)} · Baseline ${baselineRunId || "none"}`,
    },
  ];

  const watchItems = [
    paper?.latest_issue_session_id
      ? {
          tone: "negative",
          label: "Paper issue",
          body: `${paper.latest_issue_session_id}${paper?.latest_issue_error_type ? ` · ${paper.latest_issue_error_type}` : ""}`,
        }
      : {
          tone: "positive",
          label: "Paper issue watch",
          body: "No failing paper session is currently surfaced.",
        },
    brokerHasAlerts
      ? {
          tone: "negative",
          label: "Broker alerts",
          body: (broker?.alerts || []).slice(0, 2).map((alert) => `${alert.code || "alert"}${alert.session_id ? ` · ${alert.session_id}` : ""}`).join(" | "),
        }
      : {
          tone: brokerReady ? "positive" : "warning",
          label: "Broker alert watch",
          body: brokerReady ? "No broker alerts are active right now." : "Broker alerting will appear here once validations exist.",
        },
    latestFailedJob
      ? {
          tone: "warning",
          label: "Latest failed launch",
          body: `${latestFailedJob.request_id || "-"} · ${titleCase(latestFailedJob.command || "unknown")}${latestFailedJob?.ended_at ? ` · ${formatDateTime(latestFailedJob.ended_at)}` : ""}`,
        }
      : {
          tone: "positive",
          label: "Launch failure watch",
          body: "No failed launch job is currently visible in the recent job window.",
        },
    {
      tone: stepbit?.live_urls?.core_ready ? "positive" : stepbitLive ? "warning" : "",
      label: "Optional Stepbit boundary",
      body: stepbit?.live_urls?.core_ready
        ? "Stepbit app and core are available as an optional copiloted layer."
        : stepbitLive
          ? "Stepbit app is reachable but chat is not ready because core is unavailable."
          : "Stepbit remains optional and currently inactive from the shell perspective.",
    },
  ];

  const nextAction = selectPaperOpsNextAction({
    paper,
    broker,
    latestFailedJob,
    latestJob,
    latestRun,
    decisionCompareRunIds,
    baselineRunId,
  });

  return `
    <div class="tab-shell">
      <div class="artifact-top">
        <div>
          <div class="section-label">Operational surface</div>
          <h3>Paper ops</h3>
          <div class="artifact-meta">Runtime continuity for paper readiness, broker boundary, launch review, and decision follow-through.</div>
        </div>
        <div class="workflow-actions">
          <button class="ghost-btn" type="button" data-open-browser-ops="/research_ui/index.html#/ops">Browser ops</button>
          ${latestJob ? `<button class="ghost-btn" type="button" data-open-job="${escapeHtml(latestJob.request_id || "")}">Latest launch review</button>` : ""}
          ${latestRun?.run_id ? `<button class="ghost-btn" type="button" data-open-run="${escapeHtml(latestRun.run_id)}">Latest run</button>` : ""}
          ${latestRun?.run_id ? `<button class="ghost-btn" type="button" data-open-artifacts="${escapeHtml(latestRun.run_id)}">Latest artifacts</button>` : ""}
        </div>
      </div>
      <div class="tab-summary-grid">
        ${renderSummaryCard("Paper state", paperReady ? "Ready" : "Pending", paperReady ? "tone-positive" : "tone-warning")}
        ${renderSummaryCard("Latest paper state", titleCase(paper?.latest_session_status || "none"), paper?.latest_issue_session_id ? "tone-negative" : paperReady ? "tone-positive" : "tone-warning")}
        ${renderSummaryCard("Broker boundary", brokerReady ? "Visible" : "Missing", brokerHasAlerts ? "tone-negative" : brokerReady ? "tone-positive" : "tone-warning")}
        ${renderSummaryCard("Broker alerts", broker?.has_alerts ? "Review required" : "Clear", broker?.has_alerts ? "tone-negative" : "tone-positive")}
        ${renderSummaryCard("Decision compare", decisionCompareRunIds.length >= 2 ? "Ready" : "Incomplete", decisionCompareRunIds.length >= 2 ? "tone-positive" : "tone-warning")}
        ${renderSummaryCard("Latest failed launch", latestFailedJob ? "Review required" : "Clear", latestFailedJob ? "tone-warning" : "tone-positive")}
        ${renderSummaryCard("Stepbit frontend", stepbit?.live_urls?.frontend_reachable ? "Attached" : "Detached", stepbit?.live_urls?.frontend_reachable ? "tone-positive" : "tone-negative")}
        ${renderSummaryCard("Stepbit core", stepbit?.live_urls?.core_ready ? "Ready" : stepbit?.live_urls?.core_reachable ? "Partial" : "Detached", stepbit?.live_urls?.core_ready ? "tone-positive" : stepbit?.live_urls?.core_reachable ? "tone-warning" : "tone-negative")}
      </div>
      <div class="artifact-grid">
        <section class="artifact-panel">
          <div class="section-label">Now</div>
          <h3>Current operational picture</h3>
          <div class="ops-state-list">
            ${nowItems.map((item) => `
              <article class="ops-state-card tone-${escapeHtml(item.tone || "neutral")}">
                <div class="eyebrow">${escapeHtml(item.label)}</div>
                <strong>${escapeHtml(item.title)}</strong>
                <p>${escapeHtml(item.meta)}</p>
              </article>
            `).join("")}
          </div>
        </section>
        <section class="artifact-panel">
          <div class="section-label">Watch</div>
          <h3>Items worth attention</h3>
          <div class="ops-watch-list">
            ${watchItems.map((item) => `
              <article class="ops-watch-item tone-${escapeHtml(item.tone || "neutral")}">
                <strong>${escapeHtml(item.label)}</strong>
                <p>${escapeHtml(item.body)}</p>
              </article>
            `).join("")}
          </div>
        </section>
      </div>
      <section class="artifact-panel ops-next-panel">
        <div class="section-label">Next</div>
        <h3>Suggested next move</h3>
        <div class="ops-callout tone-${escapeHtml(nextAction.tone)}">${escapeHtml(nextAction.message)}</div>
        <div class="workflow-actions">
          ${latestFailedJob ? `<button class="ghost-btn" type="button" data-open-job="${escapeHtml(latestFailedJob.request_id || "")}">Review failed launch</button>` : ""}
          ${latestRun?.run_id ? `<button class="ghost-btn" type="button" data-open-run="${escapeHtml(latestRun.run_id)}">Open latest run</button>` : ""}
          ${latestRun?.run_id ? `<button class="ghost-btn" type="button" data-open-artifacts="${escapeHtml(latestRun.run_id)}">Open latest artifacts</button>` : ""}
          ${decisionCompareRunIds.length >= 2 ? `<button class="ghost-btn" type="button" data-open-shortlist-compare="true">Open decision compare</button>` : ""}
          ${baselineRunId ? `<button class="ghost-btn" type="button" data-open-run="${escapeHtml(baselineRunId)}">Open baseline</button>` : ""}
          <button class="ghost-btn" type="button" data-open-browser-ops="/research_ui/index.html#/ops">Browser ops</button>
        </div>
      </section>
      <div class="artifact-grid">
        <section class="artifact-panel">
          <div class="section-label">Paper boundary</div>
          <h3>Session health</h3>
          <dl class="metric-list compact">
            ${compareMetric("Root", paper?.root_dir || "-", "")}
            ${compareMetric("Latest session", paper?.latest_session_id || "-", "")}
            ${compareMetric("Latest issue", paper?.latest_issue_session_id || "-", "")}
            ${compareMetric("Latest issue type", paper?.latest_issue_error_type || "-", "")}
          </dl>
          ${renderOpsChipRow("Paper counts", paper?.status_counts)}
        </section>
        <section class="artifact-panel">
          <div class="section-label">Broker boundary</div>
          <h3>Submission health</h3>
          <dl class="metric-list compact">
            ${compareMetric("Latest submit", broker?.latest_submit_session_id || "-", "")}
            ${compareMetric("Submit state", broker?.latest_submit_state || "-", "")}
            ${compareMetric("Order state", broker?.latest_order_state || "-", "")}
            ${compareMetric("Latest issue", broker?.latest_issue_code || "-", "")}
          </dl>
          ${renderOpsChipRow("Broker counts", broker?.status_counts)}
          ${renderOpsChipRow("Alert counts", broker?.alert_counts)}
        </section>
      </div>
      <div class="artifact-grid">
        <section class="artifact-panel">
          <div class="section-label">Launch continuity</div>
          <h3>Recent launch job</h3>
          ${latestJob ? `
            <dl class="metric-list compact">
              ${compareMetric("Request", latestJob.request_id || "-", "")}
              ${compareMetric("Command", titleCase(latestJob.command || "unknown"), "")}
              ${compareMetric("Launch state", resolveLaunchSignal(latestJob.status, { emptyLabel: "Launch pending" }).label, resolveLaunchSignal(latestJob.status, { emptyLabel: "Launch pending" }).tone)}
              ${compareMetric("Run id", latestJob.run_id || "-", "")}
            </dl>
          ` : `<div class="empty-state">No launch jobs are available yet.</div>`}
        </section>
        <section class="artifact-panel">
          <div class="section-label">Stepbit boundary</div>
          <h3>Optional copiloted runtime</h3>
          <dl class="metric-list compact">
            ${compareMetric("Boundary note", stepbit?.boundary_note || "-", "")}
            ${compareMetric("Frontend", stepbit?.live_urls?.frontend_reachable ? "reachable" : "down", "")}
            ${compareMetric("Backend", stepbit?.live_urls?.backend_reachable ? "reachable" : "down", "")}
            ${compareMetric("Core", stepbit?.live_urls?.core_ready ? "ready" : stepbit?.live_urls?.core_reachable ? "up" : "down", "")}
          </dl>
        </section>
      </div>
    </div>
  `;
}

function renderOpsChipRow(label, counts) {
  const entries = Object.entries(counts || {}).filter(([, value]) => Number(value) > 0);
  if (!entries.length) return "";
  return `
    <div class="ops-chip-row">
      <div class="eyebrow">${escapeHtml(label)}</div>
      <div class="run-row-flags">
        ${entries.map(([key, value]) => `<span class="metric-chip">${escapeHtml(titleCase(String(key).replace(/_/g, " ")))} ${escapeHtml(formatCount(Number(value)))}</span>`).join("")}
      </div>
    </div>
  `;
}

export function describeSnapshotRefresh(snapshotStatus) {
  if (snapshotStatus?.status === "ok") {
    return {
      label: snapshotStatus.refreshPaused ? "Paused" : "Live",
      tone: snapshotStatus.refreshPaused ? "tone-warning" : "tone-positive",
      lastSuccessAt: snapshotStatus.lastSuccessAt ? formatDateTime(snapshotStatus.lastSuccessAt) : "Never",
    };
  }
  if (snapshotStatus?.status === "degraded") {
    return {
      label: snapshotStatus.refreshPaused ? "Review required" : "Degraded",
      tone: "tone-warning",
      lastSuccessAt: snapshotStatus.lastSuccessAt ? formatDateTime(snapshotStatus.lastSuccessAt) : "Never",
    };
  }
  if (snapshotStatus?.status === "error") {
    return {
      label: snapshotStatus.refreshPaused ? "Review required" : "Unavailable",
      tone: "tone-negative",
      lastSuccessAt: snapshotStatus.lastSuccessAt ? formatDateTime(snapshotStatus.lastSuccessAt) : "Never",
    };
  }
  return {
    label: "Waiting",
    tone: "tone-warning",
    lastSuccessAt: snapshotStatus?.lastSuccessAt ? formatDateTime(snapshotStatus.lastSuccessAt) : "Never",
  };
}

function collectSystemUrls(workspace, liveUrls) {
  const entries = [];
  if (workspace?.serverUrl) {
    entries.push({ label: "Research UI", url: `${workspace.serverUrl.replace(/\/$/, "")}/research_ui/index.html` });
  }
  Object.entries(liveUrls || {}).forEach(([key, value]) => {
    if (typeof value !== "string" || !/^https?:\/\//i.test(value)) return;
    entries.push({
      label: titleCase(String(key).replace(/_/g, " ")),
      url: value,
    });
  });
  return entries;
}

function collectSystemLogPreview(logs, maxChars) {
  const lines = Array.isArray(logs) ? logs.filter((entry) => typeof entry === "string" && entry.trim()) : [];
  if (!lines.length) return "";
  return formatLogPreview(lines.slice(-12).join("\n"), maxChars);
}

function buildSystemWatchItems({ workspace, snapshotStatus, brokerAlerts, latestFailedJob, launchJobs, liveUrls, latestRun }) {
  const items = [];
  if (workspace?.error) {
    items.push({
      tone: "negative",
      label: "Workspace error",
      body: workspace.error,
    });
  } else {
    items.push({
      tone: workspace?.status === "ready" ? "positive" : "warning",
      label: "Workspace bootstrap",
      body: workspace?.status === "ready"
        ? "Research UI is reachable from the desktop shell."
        : "Bootstrap is incomplete or waiting for the local server.",
    });
  }
  if (snapshotStatus?.status === "error") {
    items.push({
      tone: "negative",
      label: "Snapshot refresh",
      body: snapshotStatus.error || "The local API refresh loop is currently degraded.",
    });
  }
  if (latestFailedJob) {
    items.push({
      tone: "warning",
      label: "Latest failed launch",
      body: `${latestFailedJob.request_id || "-"} · ${titleCase(latestFailedJob.command || "unknown")} should be reviewed before trusting the current path.`,
    });
  } else {
    items.push({
      tone: launchJobs.length ? "positive" : "neutral",
      label: "Launch review",
      body: launchJobs.length ? "No failed launch is visible in the tracked recent jobs." : "No launch activity is visible yet.",
    });
  }
  if (brokerAlerts.length) {
    items.push({
      tone: "negative",
      label: "Broker boundary",
      body: brokerAlerts.slice(0, 2).map((alert) => alert.code || alert.session_id || "alert").join(" | "),
    });
  } else {
    items.push({
      tone: "positive",
      label: "Broker boundary",
      body: "No broker alerts are currently surfaced.",
    });
  }
  items.push({
    tone: liveUrls?.core_ready ? "positive" : liveUrls?.frontend_reachable || liveUrls?.backend_reachable ? "warning" : "neutral",
    label: "Optional Stepbit boundary",
    body: liveUrls?.core_ready
      ? "Frontend, backend, and core are available."
      : liveUrls?.frontend_reachable || liveUrls?.backend_reachable
        ? "Some Stepbit surfaces are reachable, but the core is not ready."
        : "Stepbit is currently inactive from the shell perspective.",
  });
  if (latestRun?.run_id) {
    items.push({
      tone: "neutral",
      label: "Latest indexed run",
      body: `${latestRun.run_id} is the freshest artifact path available for inspection.`,
    });
  }
  return items;
}

function selectPaperOpsNextAction({ paper, broker, latestFailedJob, latestJob, latestRun, decisionCompareRunIds, baselineRunId }) {
  if (latestFailedJob) {
    return {
      tone: "warning",
      message: `Start by reviewing failed launch ${latestFailedJob.request_id || "-"}. Paper health may look stable while the newest launch path is still broken.`,
    };
  }
  if (broker?.has_alerts) {
    return {
      tone: "negative",
      message: "Broker alerts are present. Inspect the broker boundary before trusting any submission-ready flow.",
    };
  }
  if (decisionCompareRunIds.length >= 2) {
    return {
      tone: "positive",
      message: "You already have enough decision runs to compare. Use shortlist compare and decide whether to keep or replace the current baseline.",
    };
  }
  if (latestRun?.run_id) {
    return {
      tone: "neutral",
      message: `Open the latest run ${latestRun.run_id} and inspect its artifacts before promoting anything toward paper.`,
    };
  }
  if (paper?.available && paper?.total_sessions) {
    return {
      tone: "neutral",
      message: `Paper health is visible with ${paper.total_sessions} tracked sessions. Next useful step is to connect that visibility back to a concrete run or decision candidate.`,
    };
  }
  if (latestJob) {
    return {
      tone: "neutral",
      message: `Recent launch activity exists (${latestJob.request_id || "-"}) but paper continuity is still thin. Review the job and then the resulting run.`,
    };
  }
  if (baselineRunId) {
    return {
      tone: "neutral",
      message: `A baseline run is pinned (${baselineRunId}). Open it and decide whether it should remain the reference before launching new paper work.`,
    };
  }
  return {
    tone: "warning",
    message: "Paper Ops is ready, but there is not enough operational history yet. Launch a run or sweep first, then come back here to review continuity.",
  };
}

export function renderJobTab(tab, ctx) {
  const job = ctx.findJob(tab.requestId) || tab.job;
  if (!job) {
    return `<div class="tab-placeholder">The requested launch job is no longer present in the current snapshot.</div>`;
  }
  if (tab.status === "loading") {
    return `<div class="tab-placeholder">Reading launch logs for ${escapeHtml(job.request_id || "unknown")}...</div>`;
  }
  if (tab.status === "error") {
    return `<div class="tab-placeholder">${escapeHtml(tab.error || "Could not load launch job details.")}</div>`;
  }

  const failureSummary = ctx.buildFailureExplanation(job, tab.stderrText || "");
  const statusSignal = resolveLaunchSignal(job.status, { emptyLabel: "Launch pending" });

  return `
    <div class="artifact-shell">
      <div class="artifact-top">
        <div>
          <div class="section-label">Launch review</div>
          <h3>${escapeHtml(job.request_id || "unknown")}</h3>
          <div class="artifact-meta">${escapeHtml(titleCase(job.command || "unknown"))} · ${escapeHtml(job.summary || "-")}</div>
        </div>
        <div class="workflow-actions">
          ${job.run_id ? `<button class="ghost-btn" type="button" data-open-run="${escapeHtml(job.run_id)}">Open run</button>` : ""}
          ${job.artifacts_href ? `<button class="ghost-btn" type="button" data-open-job-artifacts="${escapeHtml(job.request_id || "")}">Artifacts</button>` : ""}
          ${job.stderr_href ? `<button class="ghost-btn" type="button" data-open-job-link="${escapeHtml(job.stderr_href)}">Open stderr</button>` : ""}
        </div>
      </div>
      <div class="tab-summary-grid">
        ${renderSummaryCard("Launch state", statusSignal.label, statusSignal.tone)}
        ${renderSummaryCard("Started", formatDateTime(job.started_at))}
        ${renderSummaryCard("Ended", formatDateTime(job.ended_at))}
        ${renderSummaryCard("Run id", job.run_id || "-")}
      </div>
      <section class="artifact-panel">
        <div class="section-label">Failure review</div>
        <h3>Deterministic summary</h3>
        <div class="artifact-meta">${escapeHtml(failureSummary)}</div>
      </section>
      <div class="artifact-grid">
        <section class="artifact-panel">
          <div class="section-label">Stdout</div>
          <h3>Process output</h3>
          <pre class="log-preview">${escapeHtml(formatLogPreview(tab.stdoutText || "No stdout captured.", ctx.maxLogPreviewChars))}</pre>
        </section>
        <section class="artifact-panel">
          <div class="section-label">Stderr</div>
          <h3>Error output</h3>
          <pre class="log-preview">${escapeHtml(formatLogPreview(tab.stderrText || job.error_message || "No stderr captured.", ctx.maxLogPreviewChars))}</pre>
        </section>
      </div>
    </div>
  `;
}
