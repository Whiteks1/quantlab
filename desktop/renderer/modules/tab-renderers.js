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

  return `
    <div class="tab-shell">
      <div class="artifact-top">
        <div>
          <div class="section-label">Run workspace</div>
          <h3>${escapeHtml(run.run_id)}</h3>
          <div class="artifact-meta">${escapeHtml(run.ticker || "-")} · ${escapeHtml(titleCase(run.mode || "unknown"))} · ${escapeHtml(formatDateTime(run.created_at))}</div>
        </div>
        <div class="workflow-actions">
          <button class="ghost-btn" type="button" data-open-browser-run="${escapeHtml(run.run_id)}">Browser view</button>
          <button class="ghost-btn" type="button" data-open-artifacts="${escapeHtml(run.run_id)}">Artifacts</button>
          <button class="ghost-btn" type="button" data-mark-candidate="${escapeHtml(run.run_id)}">${ctx.decision.isCandidateRun(ctx.store, run.run_id) ? "Unmark candidate" : "Mark candidate"}</button>
          <button class="ghost-btn" type="button" data-shortlist-run="${escapeHtml(run.run_id)}">${ctx.decision.isShortlistedRun(ctx.store, run.run_id) ? "Remove shortlist" : "Add shortlist"}</button>
          <button class="ghost-btn" type="button" data-set-baseline="${escapeHtml(run.run_id)}">${ctx.decision.isBaselineRun(ctx.store, run.run_id) ? "Clear baseline" : "Set baseline"}</button>
          <button class="ghost-btn" type="button" data-edit-note="${escapeHtml(run.run_id)}">${candidateEntry?.note ? "Edit note" : "Add note"}</button>
        </div>
      </div>
      <div class="tab-summary-grid">
        ${renderSummaryCard("Return", formatPercent(run.total_return), toneClass(run.total_return, true))}
        ${renderSummaryCard("Sharpe", formatNumber(run.sharpe_simple))}
        ${renderSummaryCard("Drawdown", formatPercent(run.max_drawdown), toneClass(run.max_drawdown, false))}
        ${renderSummaryCard("Trades", formatCount(run.trades))}
        ${renderSummaryCard("Decision state", ctx.decision.summarizeCandidateState(ctx.store, run.run_id))}
        ${renderSummaryCard("Artifacts", fileEntries.length ? `${fileEntries.length} files` : "Pending")}
      </div>
      <div class="artifact-grid">
        <section class="artifact-panel">
          <div class="section-label">Run summary</div>
          <h3>Registry snapshot</h3>
          <dl class="metric-list compact">
            ${compareMetric("Mode", titleCase(run.mode || "unknown"), "")}
            ${compareMetric("Ticker", run.ticker || "-", "")}
            ${compareMetric("Window", `${run.start || "-"} -> ${run.end || "-"}`, "")}
            ${compareMetric("Commit", shortCommit(run.git_commit) || "-", "")}
            ${compareMetric("Path", run.path || "-", "")}
          </dl>
        </section>
        <section class="artifact-panel">
          <div class="section-label">Execution</div>
          <h3>Header and reproduce</h3>
          <dl class="metric-list compact">
            ${compareMetric("Config path", report?.header?.config_path || "-", "")}
            ${compareMetric("Config hash", report?.header?.config_hash || "-", "")}
            ${compareMetric("Python", report?.header?.python_version || "-", "")}
            ${compareMetric("Reproduce", report?.reproduce?.command || "-", "")}
          </dl>
        </section>
      </div>
      <div class="artifact-grid">
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
        <section class="artifact-panel">
          <div class="section-label">Resolved config</div>
          <h3>Effective parameters</h3>
          ${configEntries.length ? `
            <dl class="metric-list compact">
              ${configEntries.map(([label, value]) => compareMetric(label, value, "")).join("")}
            </dl>
          ` : `<div class="empty-state">No resolved config was available in the canonical report.</div>`}
        </section>
      </div>
      <div class="artifact-grid">
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
        <section class="artifact-panel">
          <div class="section-label">Workspace files</div>
          <h3>Local artifact directory</h3>
          ${renderLocalFilesList(fileEntries.slice(0, 10), detail.directoryTruncated)}
        </section>
      </div>
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

export function renderArtifactsTab(tab, ctx) {
  const run = ctx.findRun(tab.runId);
  if (!run) return `<div class="tab-placeholder">The requested run is no longer present in the registry.</div>`;
  if (tab.status === "loading") return `<div class="tab-placeholder">Reading canonical artifacts for ${escapeHtml(run.run_id)}...</div>`;
  if (tab.status === "error") return `<div class="tab-placeholder">${escapeHtml(tab.error || "Could not load artifact metadata.")}</div>`;
  const detail = tab.detail || { report: null, reportUrl: null, directoryEntries: [] };
  const report = detail.report;
  const artifacts = Array.isArray(report?.artifacts) ? report.artifacts : [];
  const primaryResult = selectPrimaryResult(run, report);
  return `
    <div class="artifact-shell">
      <div class="artifact-top">
        <div>
          <div class="section-label">Artifacts</div>
          <h3>${escapeHtml(run.run_id)}</h3>
          <div class="artifact-meta">${escapeHtml(run.ticker || "-")} · ${escapeHtml(formatDateTime(run.created_at))}</div>
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
      <div class="artifact-grid">
        <section class="artifact-panel">
          <div class="section-label">Run metadata</div>
          <h3>Window and output path</h3>
          <div class="artifact-meta">${escapeHtml(`${run.start || "-"} -> ${run.end || "-"}`)}</div>
          <div class="artifact-path">${escapeHtml(run.path || "-")}</div>
        </section>
        <section class="artifact-panel">
          <div class="section-label">Artifact manifest</div>
          <h3>Files</h3>
          ${artifacts.length ? `<div class="artifact-list">
            ${artifacts.map((artifact) => {
              const href = buildRunArtifactHref(run.path, artifact.file_name);
              return `<button class="artifact-link" type="button" data-open-external="${escapeHtml(href)}"><span>${escapeHtml(artifact.file_name)}</span><span>${escapeHtml(formatBytes(artifact.size_bytes))}</span></button>`;
            }).join("")}
          </div>` : `<div class="empty-state">The canonical report does not expose an artifact manifest for this run.</div>`}
        </section>
      </div>
      <div class="artifact-grid">
        <section class="artifact-panel">
          <div class="section-label">Resolved config</div>
          <h3>Decision context</h3>
          ${renderCompactEntryList(summarizeObjectEntries(report?.config_resolved))}
        </section>
        <section class="artifact-panel">
          <div class="section-label">Local files</div>
          <h3>Run directory</h3>
          ${renderLocalFilesList(detail.directoryEntries || [], detail.directoryTruncated)}
        </section>
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

export function renderPaperOpsTab(ctx) {
  const paper = ctx.snapshot?.paperHealth || null;
  const broker = ctx.snapshot?.brokerHealth || null;
  const stepbit = ctx.snapshot?.stepbitWorkspace || null;
  const latestJob = ctx.getJobs()[0] || null;
  return `
    <div class="tab-shell">
      <div class="artifact-top">
        <div>
          <div class="section-label">Operational surface</div>
          <h3>Paper ops</h3>
          <div class="artifact-meta">Read-only runtime visibility for paper, broker boundary, launch state, and Stepbit readiness.</div>
        </div>
        <div class="workflow-actions">
          <button class="ghost-btn" type="button" data-open-browser-ops="/research_ui/index.html#/ops">Browser ops</button>
          ${latestJob ? `<button class="ghost-btn" type="button" data-open-job="${escapeHtml(latestJob.request_id || "")}">Latest launch review</button>` : ""}
          ${ctx.getLatestRun()?.run_id ? `<button class="ghost-btn" type="button" data-open-run="${escapeHtml(ctx.getLatestRun().run_id)}">Latest run</button>` : ""}
        </div>
      </div>
      <div class="tab-summary-grid">
        ${renderSummaryCard("Paper sessions", String(paper?.total_sessions ?? 0))}
        ${renderSummaryCard("Latest paper status", titleCase(paper?.latest_session_status || "none"))}
        ${renderSummaryCard("Broker validations", String(broker?.total_sessions ?? 0))}
        ${renderSummaryCard("Broker alerts", broker?.has_alerts ? "Present" : "None", broker?.has_alerts ? "tone-negative" : "tone-positive")}
        ${renderSummaryCard("Stepbit frontend", stepbit?.live_urls?.frontend_reachable ? "Up" : "Down", stepbit?.live_urls?.frontend_reachable ? "tone-positive" : "tone-negative")}
        ${renderSummaryCard("Stepbit core", stepbit?.live_urls?.core_ready ? "Ready" : stepbit?.live_urls?.core_reachable ? "Up" : "Down", stepbit?.live_urls?.core_ready ? "tone-positive" : stepbit?.live_urls?.core_reachable ? "" : "tone-negative")}
      </div>
      <div class="artifact-grid">
        <section class="artifact-panel">
          <div class="section-label">Paper boundary</div>
          <h3>Health snapshot</h3>
          <dl class="metric-list compact">
            ${compareMetric("Root", paper?.root_dir || "-", "")}
            ${compareMetric("Latest session", paper?.latest_session_id || "-", "")}
            ${compareMetric("Latest issue", paper?.latest_issue_session_id || "-", "")}
            ${compareMetric("Latest issue type", paper?.latest_issue_error_type || "-", "")}
          </dl>
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
