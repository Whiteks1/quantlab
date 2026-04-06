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

export function renderSummaryCard(label, value, tone = "") {
  return `<article class="summary-card"><div class="label">${escapeHtml(label)}</div><div class="value ${escapeHtml(tone)}">${escapeHtml(value)}</div></article>`;
}

export function compareMetric(label, value, extraClass) {
  return `<div class="${escapeHtml(extraClass)}"><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`;
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
    ? `<dl class="metric-list compact">${entries.map(([label, value]) => compareMetric(label, value, "")).join("")}</dl>`
    : `<div class="empty-state">No structured config entries were available.</div>`;
}

export function renderLocalFilesList(entries, truncated = false) {
  if (!entries.length) {
    return `<div class="empty-state">No local files were discoverable in the run directory.</div>`;
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
      <div class="run-row-metrics">
        <span class="metric-chip ${toneClass(run.total_return, true)}">Return ${formatPercent(run.total_return)}</span>
        <span class="metric-chip">Sharpe ${formatNumber(run.sharpe_simple)}</span>
        <span class="metric-chip ${toneClass(run.max_drawdown, false)}">Drawdown ${formatPercent(run.max_drawdown)}</span>
      </div>
    `
    : `<div class="empty-state">This run is no longer indexed, but the decision record is still preserved locally.</div>`;
  const noteText = entry.note ? escapeHtml(entry.note) : "No note yet.";
  return `
    <article class="candidate-card ${forceShow ? "baseline-card" : ""}">
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
      <div class="workflow-actions">
        ${run ? `<button class="ghost-btn" type="button" data-open-run="${escapeHtml(entry.run_id)}">Open run</button>` : ""}
        ${run ? `<button class="ghost-btn" type="button" data-open-artifacts="${escapeHtml(entry.run_id)}">Artifacts</button>` : ""}
        <button class="ghost-btn" type="button" data-edit-note="${escapeHtml(entry.run_id)}">${entry.note ? "Edit note" : "Add note"}</button>
        <button class="ghost-btn" type="button" data-shortlist-run="${escapeHtml(entry.run_id)}">${entry.shortlisted ? "Remove shortlist" : "Add shortlist"}</button>
        <button class="ghost-btn" type="button" data-set-baseline="${escapeHtml(entry.run_id)}">${decision.isBaselineRun(ctx.store, entry.run_id) ? "Clear baseline" : "Set baseline"}</button>
        <button class="ghost-btn" type="button" data-mark-candidate="${escapeHtml(entry.run_id)}">Remove candidate</button>
      </div>
    </article>
  `;
}

export function renderRunsTab(_tab, ctx) {
  const runs = ctx.getRuns();
  return `
    <div class="tab-shell runs-tab">
      <div class="artifact-top">
        <div>
          <div class="section-label">Run explorer</div>
          <h3>Runs</h3>
          <div class="artifact-meta">Native execution log and traceability surface for indexed runs inside QuantLab Desktop.</div>
        </div>
        <div class="workflow-actions">
          <button class="ghost-btn" type="button" data-open-runs-legacy="true">Open legacy view</button>
        </div>
      </div>
      ${renderRunsTable(runs, ctx.store, ctx.decision)}
    </div>
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
  const hasDecisionPeers = ctx.decision.isBaselineRun(ctx.store, run.run_id)
    ? ctx.decision.getCandidateEntriesResolved(ctx.store, ctx.findRun).length > 1
    : Boolean(ctx.store.baseline_run_id || ctx.decision.isShortlistedRun(ctx.store, run.run_id));
  const decisionNote = candidateEntry?.note ? escapeHtml(candidateEntry.note) : "No local decision note yet.";
  const continuityState = latestRelatedJob
    ? `${titleCase(latestRelatedJob.status || "unknown")} · ${formatDateTime(latestRelatedJob.created_at)}`
    : "No linked launch job";
  const relatedJobTone = latestRelatedJob?.status === "failed" ? "tone-down" : latestRelatedJob?.status === "succeeded" ? "tone-up" : "";
  return `
    <div class="tab-shell run-detail-shell">
      ${renderRunIdentityHeader(run, ctx, latestRelatedJob)}
      ${renderRunMetricsSummary(run)}
      <div class="run-detail-grid">
        <div class="run-detail-main">
          ${renderRunDecisionBlock(run, ctx, candidateEntry, decisionNote, hasDecisionPeers)}
          ${renderRunConfigProvenanceBlock(run, report)}
        </div>
        <div class="run-detail-side">
          ${renderRunArtifactsContinuityBlock(run, fileEntries, detail, latestRelatedJob, continuityState, sweepEntries)}
        </div>
      </div>
      <div class="run-detail-deep">
        ${renderRunPrimaryResultBlock(primaryResult)}
        ${renderRunResolvedConfigBlock(configEntries)}
        ${renderRunLaunchReviewBlock(run, latestRelatedJob, relatedJobTone)}
        ${renderRunTopResultsBlock(topResults)}
        ${renderRunSweepLinkageBlock(ctx, sweepEntries)}
      </div>
    </div>
  `;
}

function renderRunIdentityHeader(run, ctx, latestRelatedJob) {
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
  return `
    <section class="artifact-panel">
      <div class="section-label">Decision / validation</div>
      <h3>What should happen next</h3>
      <div class="run-row-flags">${renderCandidateFlags(ctx.store, run.run_id, ctx.decision)}</div>
      <div class="artifact-meta">Current state: ${escapeHtml(ctx.decision.summarizeCandidateState(ctx.store, run.run_id))}</div>
      <div class="candidate-note">${decisionNote}</div>
      <div class="workflow-actions">
        <button class="ghost-btn" type="button" data-mark-candidate="${escapeHtml(run.run_id)}">${ctx.decision.isCandidateRun(ctx.store, run.run_id) ? "Unmark candidate" : "Mark candidate"}</button>
        <button class="ghost-btn" type="button" data-shortlist-run="${escapeHtml(run.run_id)}">${ctx.decision.isShortlistedRun(ctx.store, run.run_id) ? "Remove shortlist" : "Add shortlist"}</button>
        <button class="ghost-btn" type="button" data-set-baseline="${escapeHtml(run.run_id)}">${ctx.decision.isBaselineRun(ctx.store, run.run_id) ? "Clear baseline" : "Set baseline"}</button>
        <button class="ghost-btn" type="button" data-edit-note="${escapeHtml(run.run_id)}">${candidateEntry?.note ? "Edit note" : "Add note"}</button>
      </div>
      <div class="workflow-actions">
        <button class="ghost-btn" type="button" data-open-decision-compare="${escapeHtml(run.run_id)}" ${hasDecisionPeers ? "" : "disabled"}>Compare with decision set</button>
        <button class="ghost-btn" type="button" data-open-candidates="true">Open candidates</button>
      </div>
      ${hasDecisionPeers ? `<div class="artifact-meta">This run can be compared directly against the current shortlist or baseline.</div>` : `<div class="artifact-meta">Pin a baseline or shortlist another run to enable decision compare from here.</div>`}
    </section>
  `;
}

function renderRunConfigProvenanceBlock(run, report) {
  return `
    <section class="artifact-panel">
      <div class="section-label">Config + provenance</div>
      <h3>How this run was produced</h3>
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
    </section>
  `;
}

function renderRunArtifactsContinuityBlock(run, fileEntries, detail, latestRelatedJob, continuityState, sweepEntries) {
  return `
    <section class="artifact-panel">
      <div class="section-label">Artifacts + continuity</div>
      <h3>Evidence and operational links</h3>
      <dl class="metric-list compact">
        ${compareMetric("Artifacts", fileEntries.length ? `${fileEntries.length} files` : "Pending", "")}
        ${compareMetric("Launch continuity", continuityState, "")}
        ${compareMetric("Sweep linkage", sweepEntries.length ? `${sweepEntries.length} tracked rows` : "None", "")}
      </dl>
      <div class="workflow-actions">
        <button class="ghost-btn" type="button" data-open-artifacts="${escapeHtml(run.run_id)}">Inspect artifacts</button>
        <button class="ghost-btn" type="button" data-open-browser-run="${escapeHtml(run.run_id)}">Browser view</button>
        ${latestRelatedJob ? `<button class="ghost-btn" type="button" data-open-related-job="${escapeHtml(run.run_id)}">Latest launch review</button>` : ""}
        ${latestRelatedJob?.stderr_href ? `<button class="ghost-btn" type="button" data-open-job-link="${escapeHtml(latestRelatedJob.stderr_href)}">Open stderr in browser</button>` : ""}
      </div>
      <div class="section-label">Workspace files</div>
      <h3>Local artifact directory</h3>
      ${renderLocalFilesList(fileEntries.slice(0, 10), detail.directoryTruncated)}
    </section>
  `;
}

function renderRunPrimaryResultBlock(primaryResult) {
  return `
    <section class="artifact-panel">
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
    </section>
  `;
}

function renderRunResolvedConfigBlock(configEntries) {
  return `
    <section class="artifact-panel">
      <div class="section-label">Resolved config</div>
      <h3>Effective parameters</h3>
      ${configEntries.length ? `
        <dl class="metric-list compact">
          ${configEntries.map(([label, value]) => compareMetric(label, value, "")).join("")}
        </dl>
      ` : `<div class="empty-state">No resolved config was available in the canonical report.</div>`}
    </section>
  `;
}

function renderRunLaunchReviewBlock(run, latestRelatedJob, relatedJobTone) {
  return `
    <section class="artifact-panel">
      <div class="section-label">Launch review</div>
      <h3>${escapeHtml(latestRelatedJob ? `Latest job ${latestRelatedJob.request_id}` : "No linked launch job")}</h3>
      ${latestRelatedJob ? `
        <dl class="metric-list compact">
          ${compareMetric("Status", titleCase(latestRelatedJob.status || "unknown"), relatedJobTone)}
          ${compareMetric("Created", formatDateTime(latestRelatedJob.created_at), "")}
          ${compareMetric("Command", latestRelatedJob.command || "-", "")}
          ${compareMetric("Request", latestRelatedJob.request_id || "-", "")}
        </dl>
        <div class="workflow-actions">
          <button class="ghost-btn" type="button" data-open-related-job="${escapeHtml(run.run_id)}">Open launch review</button>
          ${latestRelatedJob.stderr_href ? `<button class="ghost-btn" type="button" data-open-job-link="${escapeHtml(latestRelatedJob.stderr_href)}">Open stderr in browser</button>` : ""}
        </div>
      ` : `<div class="empty-state">This run does not currently expose a launch job in the local launch registry.</div>`}
    </section>
  `;
}

function renderRunTopResultsBlock(topResults) {
  return `
    <section class="artifact-panel">
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
    </section>
  `;
}

function renderRunSweepLinkageBlock(ctx, sweepEntries) {
  return `
    <section class="artifact-panel">
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
    </section>
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
  return `
    <div class="compare-shell">
      <div class="tab-summary-grid">
        ${renderSummaryCard("Compared runs", String(runs.length))}
        ${renderSummaryCard("Ranking metric", titleCase(rankMetric.replace("_", " ")))}
        ${renderSummaryCard("Winner", `${winner.run_id} · ${formatMetricForDisplay(winner[rankMetric], rankMetric)}`, rankMetric === "max_drawdown" ? toneClass(winner.max_drawdown, false) : toneClass(winner[rankMetric], true))}
        ${renderSummaryCard("Runner-up", runnerUp ? `${runnerUp.run_id} · ${formatMetricForDisplay(runnerUp[rankMetric], rankMetric)}` : "-")}
        ${renderSummaryCard("Baseline in set", includedBaseline ? includedBaseline.run_id : "No")}
        ${renderSummaryCard("Shortlisted in set", String(runs.filter((run) => ctx.decision.isShortlistedRun(ctx.store, run.run_id)).length))}
      </div>
      <section class="artifact-panel">
        <div class="section-label">Decision actions</div>
        <h3>Promote, shortlist, or baseline the winner</h3>
        <div class="workflow-actions">
          <button class="ghost-btn" type="button" data-open-run="${escapeHtml(winner.run_id)}">Open winner</button>
          <button class="ghost-btn" type="button" data-open-artifacts="${escapeHtml(winner.run_id)}">Winner artifacts</button>
          <button class="ghost-btn" type="button" data-mark-candidate="${escapeHtml(winner.run_id)}">${ctx.decision.isCandidateRun(ctx.store, winner.run_id) ? "Unmark candidate" : "Mark candidate"}</button>
          <button class="ghost-btn" type="button" data-shortlist-run="${escapeHtml(winner.run_id)}">${ctx.decision.isShortlistedRun(ctx.store, winner.run_id) ? "Remove shortlist" : "Add shortlist"}</button>
          <button class="ghost-btn" type="button" data-set-baseline="${escapeHtml(winner.run_id)}">${ctx.decision.isBaselineRun(ctx.store, winner.run_id) ? "Clear baseline" : "Set baseline"}</button>
        </div>
        <div class="workflow-actions compare-rank-actions">
          ${["sharpe_simple", "total_return", "max_drawdown", "trades"].map((metric) => `
            <button class="ghost-btn ${rankMetric === metric ? "is-selected" : ""}" type="button" data-compare-rank="${escapeHtml(metric)}">${escapeHtml(titleCase(metric.replace("_", " ")))}</button>
          `).join("")}
        </div>
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
      <div class="compare-grid">
        ${rankedRuns.map((run, index) => `
          <article class="compare-card">
            <div class="artifact-top">
              <div>
                <div class="section-label">${escapeHtml(titleCase(run.mode || "unknown"))}</div>
                <h3>${escapeHtml(run.run_id)}</h3>
              </div>
              <div class="workflow-actions">
                <button class="ghost-btn" type="button" data-open-run="${escapeHtml(run.run_id)}">Open run</button>
                <button class="ghost-btn" type="button" data-open-artifacts="${escapeHtml(run.run_id)}">Artifacts</button>
              </div>
            </div>
            <div class="compare-meta">${escapeHtml(run.ticker || "-")} · ${escapeHtml(formatDateTime(run.created_at))} · rank #${index + 1}</div>
            <div class="run-row-flags">${renderCandidateFlags(ctx.store, run.run_id, ctx.decision)}</div>
            <dl class="metric-list">
              ${compareMetric("Return", formatPercent(run.total_return), toneClass(run.total_return, true))}
              ${compareMetric("Sharpe", formatNumber(run.sharpe_simple), "")}
              ${compareMetric("Drawdown", formatPercent(run.max_drawdown), toneClass(run.max_drawdown, false))}
              ${compareMetric("Trades", formatCount(run.trades), "")}
              ${compareMetric("Window", `${run.start || "-"} -> ${run.end || "-"}`, "")}
              ${compareMetric("Commit", shortCommit(run.git_commit) || "-", "")}
            </dl>
            <div class="workflow-actions">
              <button class="ghost-btn" type="button" data-mark-candidate="${escapeHtml(run.run_id)}">${ctx.decision.isCandidateRun(ctx.store, run.run_id) ? "Unmark candidate" : "Mark candidate"}</button>
              <button class="ghost-btn" type="button" data-shortlist-run="${escapeHtml(run.run_id)}">${ctx.decision.isShortlistedRun(ctx.store, run.run_id) ? "Remove shortlist" : "Add shortlist"}</button>
              <button class="ghost-btn" type="button" data-set-baseline="${escapeHtml(run.run_id)}">${ctx.decision.isBaselineRun(ctx.store, run.run_id) ? "Clear baseline" : "Set baseline"}</button>
            </div>
          </article>
        `).join("")}
      </div>
    </div>
  `;
}

function renderRunsTable(runs, store, decision) {
  if (!Array.isArray(runs) || !runs.length) {
    return `<div class="empty-state">No runs are indexed yet. Launch a run or wait for canonical artifacts to appear.</div>`;
  }
  return `
    <div class="runs-table-wrap">
      <table class="runs-table">
        <thead>
          <tr>
            <th>Run</th>
            <th>Mode</th>
            <th>Ticker</th>
            <th>Created</th>
            <th>Commit</th>
            <th>Return</th>
            <th>Sharpe</th>
            <th>Drawdown</th>
            <th>Trades</th>
            <th>Flags</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${runs.map((run) => renderRunsRow(run, store, decision)).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderRunsRow(run, store, decision) {
  const runId = run?.run_id || "";
  const commitLabel = shortCommit(run?.git_commit) || "-";
  const candidateLabel = decision.isCandidateRun(store, runId) ? "Unmark candidate" : "Mark candidate";
  return `
    <tr class="runs-row">
      <td class="mono-cell">${escapeHtml(runId)}</td>
      <td>${escapeHtml(titleCase(run?.mode || "unknown"))}</td>
      <td>${escapeHtml(run?.ticker || "-")}</td>
      <td>${escapeHtml(formatDateTime(run?.created_at))}</td>
      <td class="mono-cell">${escapeHtml(commitLabel)}</td>
      <td class="${escapeHtml(toneClass(run?.total_return, true))}">${escapeHtml(formatPercent(run?.total_return))}</td>
      <td>${escapeHtml(formatNumber(run?.sharpe_simple))}</td>
      <td class="${escapeHtml(toneClass(run?.max_drawdown, false))}">${escapeHtml(formatPercent(run?.max_drawdown))}</td>
      <td>${escapeHtml(formatCount(run?.trades))}</td>
      <td><div class="run-flags-cell">${renderCandidateFlags(store, runId, decision)}</div></td>
      <td>
        <div class="runs-row-actions">
          <button class="ghost-btn" type="button" data-open-run="${escapeHtml(runId)}">Open run</button>
          <button class="ghost-btn" type="button" data-open-artifacts="${escapeHtml(runId)}">Artifacts</button>
          <button class="ghost-btn" type="button" data-mark-candidate="${escapeHtml(runId)}">${escapeHtml(candidateLabel)}</button>
        </div>
      </td>
    </tr>
  `;
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
        <div class="workflow-actions">
          <button class="ghost-btn" type="button" data-open-run="${escapeHtml(run.run_id)}">Open run</button>
          <button class="ghost-btn" type="button" data-mark-candidate="${escapeHtml(run.run_id)}">${ctx.decision.isCandidateRun(ctx.store, run.run_id) ? "Unmark candidate" : "Mark candidate"}</button>
          <button class="ghost-btn" type="button" data-shortlist-run="${escapeHtml(run.run_id)}">${ctx.decision.isShortlistedRun(ctx.store, run.run_id) ? "Remove shortlist" : "Add shortlist"}</button>
          <button class="ghost-btn" type="button" data-set-baseline="${escapeHtml(run.run_id)}">${ctx.decision.isBaselineRun(ctx.store, run.run_id) ? "Clear baseline" : "Set baseline"}</button>
          ${detail.reportUrl ? `<button class="ghost-btn" type="button" data-open-external="${escapeHtml(detail.reportUrl)}">Raw report</button>` : ""}
        </div>
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
  const shortlistEntries = allEntries.filter((entry) => entry.shortlisted);
  const visibleEntries = filter === "shortlist"
    ? shortlistEntries
    : filter === "baseline"
    ? allEntries.filter((entry) => entry.run_id === ctx.store.baseline_run_id)
    : allEntries;

  return `
    <div class="tab-shell">
      <div class="artifact-top">
        <div>
          <div class="section-label">Decision layer</div>
          <h3>Candidates and shortlist</h3>
          <div class="artifact-meta">Persisted locally in QuantLab Desktop. This is the minimum layer that turns observation into choice.</div>
        </div>
        <div class="workflow-actions">
          <button class="ghost-btn" type="button" data-open-shortlist-compare="true">Open shortlist compare</button>
          ${ctx.store.baseline_run_id ? `<button class="ghost-btn" type="button" data-open-run="${escapeHtml(ctx.store.baseline_run_id)}">Open baseline</button>` : ""}
        </div>
      </div>
      <div class="tab-summary-grid">
        ${renderSummaryCard("Candidates", String(allEntries.length))}
        ${renderSummaryCard("Shortlisted", String(shortlistEntries.length))}
        ${renderSummaryCard("Baseline", ctx.store.baseline_run_id || "None")}
        ${renderSummaryCard("Indexed runs", String(ctx.getRuns().length))}
      </div>
      <section class="artifact-panel">
        <div class="section-label">Filters</div>
        <h3>Focus the decision queue</h3>
        <div class="workflow-actions compare-rank-actions">
          ${["all", "shortlist", "baseline"].map((option) => `
            <button class="ghost-btn ${filter === option ? "is-selected" : ""}" type="button" data-candidates-filter="${escapeHtml(option)}">${escapeHtml(titleCase(option))}</button>
          `).join("")}
        </div>
      </section>
      ${ctx.store.baseline_run_id ? `
        <section class="artifact-panel">
          <div class="section-label">Pinned reference</div>
          <h3>Baseline</h3>
          ${renderCandidateCard(
            ctx.decision.getCandidateEntryResolved(ctx.store, ctx.store.baseline_run_id, ctx.findRun) ||
              ctx.decision.buildMissingCandidateEntry(ctx.store.baseline_run_id, ctx.findRun),
            true,
            ctx,
          )}
        </section>
      ` : ""}
      <section class="artifact-panel">
        <div class="section-label">${escapeHtml(titleCase(filter))}</div>
        <h3>Candidate list</h3>
        ${visibleEntries.length ? `<div class="candidate-list">${visibleEntries.map((entry) => renderCandidateCard(entry, false, ctx)).join("")}</div>` : `<div class="empty-state">No runs match this candidate filter yet.</div>`}
      </section>
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
      <div class="workflow-actions">
        <button class="ghost-btn" type="button" data-sweep-track-entry="${escapeHtml(entry.entry_id)}">${ctx.sweepDecision.isTracked(ctx.sweepDecisionStore, entry.entry_id) ? "Untrack" : "Track"}</button>
        <button class="ghost-btn" type="button" data-sweep-shortlist-entry="${escapeHtml(entry.entry_id)}">${ctx.sweepDecision.isShortlisted(ctx.sweepDecisionStore, entry.entry_id) ? "Remove shortlist" : "Add shortlist"}</button>
        <button class="ghost-btn" type="button" data-sweep-baseline-entry="${escapeHtml(entry.entry_id)}">${ctx.sweepDecision.isBaseline(ctx.sweepDecisionStore, entry.entry_id) ? "Clear baseline" : "Set baseline"}</button>
        <button class="ghost-btn" type="button" data-sweep-note-entry="${escapeHtml(entry.entry_id)}">${note ? "Edit note" : "Add note"}</button>
        ${configPath ? `<button class="ghost-btn" type="button" data-experiment-launch-config="${escapeHtml(configPath)}">Launch sweep</button>` : ""}
        ${sweep?.path ? `<button class="ghost-btn" type="button" data-experiment-open-path="${escapeHtml(sweep.path)}">Open folder</button>` : ""}
      </div>
    </article>
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
        ${renderSummaryCard("Paper sessions", String(paper?.total_sessions ?? 0), paperReady ? "tone-positive" : "")}
        ${renderSummaryCard("Latest paper status", titleCase(paper?.latest_session_status || "none"), paper?.latest_issue_session_id ? "tone-negative" : paperReady ? "tone-positive" : "")}
        ${renderSummaryCard("Broker boundary", brokerReady ? "Visible" : "Missing", brokerHasAlerts ? "tone-negative" : brokerReady ? "tone-positive" : "tone-warning")}
        ${renderSummaryCard("Broker alerts", broker?.has_alerts ? "Present" : "None", broker?.has_alerts ? "tone-negative" : "tone-positive")}
        ${renderSummaryCard("Decision compare", decisionCompareRunIds.length ? String(decisionCompareRunIds.length) : "0", decisionCompareRunIds.length >= 2 ? "tone-positive" : "")}
        ${renderSummaryCard("Latest failed launch", latestFailedJob ? titleCase(latestFailedJob.command || "failed") : "None", latestFailedJob ? "tone-warning" : "tone-positive")}
        ${renderSummaryCard("Stepbit frontend", stepbit?.live_urls?.frontend_reachable ? "Up" : "Down", stepbit?.live_urls?.frontend_reachable ? "tone-positive" : "tone-negative")}
        ${renderSummaryCard("Stepbit core", stepbit?.live_urls?.core_ready ? "Ready" : stepbit?.live_urls?.core_reachable ? "Up" : "Down", stepbit?.live_urls?.core_ready ? "tone-positive" : stepbit?.live_urls?.core_reachable ? "" : "tone-negative")}
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
              ${compareMetric("Status", titleCase(latestJob.status || "unknown"), latestJob.status === "failed" ? "tone-negative" : latestJob.status === "succeeded" ? "tone-positive" : "")}
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
  const statusTone = job.status === "succeeded" ? "tone-positive" : job.status === "failed" ? "tone-negative" : "";

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
        ${renderSummaryCard("Status", titleCase(job.status || "unknown"), statusTone)}
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
