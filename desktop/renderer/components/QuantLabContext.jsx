import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import * as decisionStore from '../modules/decision-store.js';
import * as sweepDecisionStore from '../modules/sweep-decision-store.js';
import { buildRunArtifactHref, uniqueRunIds } from '../modules/utils.js';

const CONFIG = {
  runsIndexPath: '/outputs/runs/runs_index.json',
  localRunsIndexPath: 'outputs/runs/runs_index.json',
  launchControlPath: '/api/launch-control',
  paperHealthPath: '/api/paper-sessions-health',
  brokerHealthPath: '/api/broker-submissions-health',
  stepbitWorkspacePath: '/api/stepbit-workspace',
  detailArtifacts: ['report.json', 'run_report.json'],
  experimentsConfigDir: 'configs/experiments',
  sweepsOutputDir: 'outputs/sweeps',
  maxCandidateCompare: 4,
  maxExperimentsConfigs: 12,
  maxRecentSweeps: 8,
};

const INITIAL_WORKSPACE = {
  status: 'starting',
  serverUrl: null,
  logs: [],
  error: null,
  source: null,
};

const INITIAL_EXPERIMENTS = {
  status: 'idle',
  configs: [],
  sweeps: [],
  error: null,
  updatedAt: null,
};

/**
 * QuantLabContext provides the React runtime with state, data accessors,
 * and actions without depending on app-legacy.js globals.
 */
export const QuantLabContext = createContext(null);

export function useQuantLab() {
  const context = useContext(QuantLabContext);
  if (!context) {
    throw new Error('useQuantLab must be called within QuantLabContext.Provider');
  }
  return context;
}

export const useQuantLabContext = useQuantLab;

function getBridge() {
  return window.quantlabDesktop;
}

function createRunsTab() {
  return {
    id: 'runs-native',
    kind: 'runs',
    navKind: 'runs',
    title: 'Runs',
  };
}

function normalizeRunsRegistry(registry) {
  if (Array.isArray(registry)) return { runs: registry };
  if (registry && typeof registry === 'object') {
    return {
      ...registry,
      runs: Array.isArray(registry.runs) ? registry.runs : [],
    };
  }
  return { runs: [] };
}

function createSnapshotStatus(source, error = null) {
  if (error) {
    return {
      status: 'degraded',
      error: error.message || String(error),
      source,
      lastSuccessAt: null,
      consecutiveErrors: 1,
      refreshPaused: false,
    };
  }
  if (source === 'none') {
    return {
      status: 'idle',
      error: null,
      source,
      lastSuccessAt: null,
      consecutiveErrors: 0,
      refreshPaused: false,
    };
  }
  return {
    status: 'ok',
    error: null,
    source,
    lastSuccessAt: new Date().toISOString(),
    consecutiveErrors: 0,
    refreshPaused: false,
  };
}

function joinProjectPath(basePath, fileName) {
  const base = String(basePath || '').replace(/[\\/]+$/, '');
  return `${base}\\${fileName}`;
}

async function readOptionalJson(targetPath) {
  try {
    return await getBridge().readProjectJson(targetPath);
  } catch (_error) {
    return null;
  }
}

async function requestOptionalJson(relativePath) {
  try {
    return await getBridge().requestJson(relativePath);
  } catch (_error) {
    return null;
  }
}

async function requestOptionalText(relativePath) {
  if (!relativePath) return '';
  try {
    return await getBridge().requestText(relativePath);
  } catch (_error) {
    return '';
  }
}

async function loadRunsRegistry(workspace) {
  let source = 'none';
  let primaryError = null;

  if (workspace?.serverUrl) {
    try {
      const runsRegistry = normalizeRunsRegistry(
        await getBridge().requestJson(CONFIG.runsIndexPath)
      );
      return { runsRegistry, source: 'api', primaryError: null };
    } catch (error) {
      primaryError = error;
    }
  }

  try {
    const runsRegistry = normalizeRunsRegistry(
      await getBridge().readProjectJson(CONFIG.localRunsIndexPath)
    );
    source = 'local';
    return { runsRegistry, source, primaryError };
  } catch (error) {
    return { runsRegistry: { runs: [] }, source, primaryError: primaryError || error };
  }
}

async function loadSnapshot(workspace) {
  const { runsRegistry, source, primaryError } = await loadRunsRegistry(workspace);
  const canRequestApi = Boolean(workspace?.serverUrl);

  const [launchControl, paperHealth, brokerHealth, stepbitWorkspace] = canRequestApi
    ? await Promise.all([
        requestOptionalJson(CONFIG.launchControlPath),
        requestOptionalJson(CONFIG.paperHealthPath),
        requestOptionalJson(CONFIG.brokerHealthPath),
        requestOptionalJson(CONFIG.stepbitWorkspacePath),
      ])
    : [null, null, null, null];

  return {
    snapshot: {
      runsRegistry,
      launchControl: launchControl || { jobs: [] },
      paperHealth: paperHealth || null,
      brokerHealth: brokerHealth || null,
      stepbitWorkspace: stepbitWorkspace || null,
    },
    snapshotStatus: createSnapshotStatus(source, primaryError),
  };
}

async function loadExperimentsWorkspace() {
  try {
    const [configsListing, sweepsListing] = await Promise.all([
      getBridge().listDirectory(CONFIG.experimentsConfigDir, 0),
      getBridge().listDirectory(CONFIG.sweepsOutputDir, 0),
    ]);

    const configs = (configsListing.entries || [])
      .filter((entry) => entry.kind === 'file' && /\.ya?ml$/i.test(entry.name))
      .sort((left, right) => String(right.modified_at || '').localeCompare(String(left.modified_at || '')))
      .slice(0, CONFIG.maxExperimentsConfigs)
      .map((entry) => ({
        name: entry.name,
        path: entry.path,
        relativePath: entry.relative_path || entry.name,
        modifiedAt: entry.modified_at,
        sizeBytes: entry.size_bytes,
        previewText: '',
      }));

    const sweeps = (sweepsListing.entries || [])
      .filter((entry) => entry.kind === 'directory' && entry.depth === 0)
      .sort((left, right) => String(right.modified_at || '').localeCompare(String(left.modified_at || '')))
      .slice(0, CONFIG.maxRecentSweeps)
      .map((entry) => ({
        run_id: entry.name,
        path: entry.path,
        mode: 'sweep',
        configPath: '',
        configName: '',
        decisionRows: [],
        hasStructuredData: false,
      }));

    return {
      status: 'ready',
      configs,
      sweeps,
      error: null,
      updatedAt: new Date().toISOString(),
    };
  } catch (error) {
    return {
      ...INITIAL_EXPERIMENTS,
      status: 'error',
      error: error.message || String(error),
      updatedAt: new Date().toISOString(),
    };
  }
}

function buildCandidateEntry(runId, existing = null) {
  const now = new Date().toISOString();
  return {
    run_id: runId,
    note: existing?.note || '',
    shortlisted: Boolean(existing?.shortlisted),
    created_at: existing?.created_at || now,
    updated_at: now,
  };
}

export function useQuantLabContextValue() {
  const [state, setState] = useState({
    workspace: INITIAL_WORKSPACE,
    snapshot: {
      runsRegistry: { runs: [] },
      launchControl: { jobs: [] },
      paperHealth: null,
      brokerHealth: null,
      stepbitWorkspace: null,
    },
    snapshotStatus: createSnapshotStatus('none'),
    candidatesStore: decisionStore.defaultCandidatesStore(),
    sweepDecisionStore: sweepDecisionStore.defaultSweepDecisionStore(),
    selectedRunIds: [],
    tabs: [createRunsTab()],
    activeTabId: 'runs-native',
    experimentsWorkspace: INITIAL_EXPERIMENTS,
  });

  const getRuns = useCallback(() => {
    return Array.isArray(state.snapshot?.runsRegistry?.runs)
      ? state.snapshot.runsRegistry.runs
      : [];
  }, [state.snapshot]);

  const findRun = useCallback((runId) => {
    return getRuns().find((run) => run.run_id === runId) || null;
  }, [getRuns]);

  const getJobs = useCallback(() => {
    return Array.isArray(state.snapshot?.launchControl?.jobs)
      ? state.snapshot.launchControl.jobs
      : [];
  }, [state.snapshot]);

  const findJob = useCallback((requestId) => {
    return getJobs().find((job) => job.request_id === requestId) || null;
  }, [getJobs]);

  const getLatestRun = useCallback(() => getRuns()[0] || null, [getRuns]);
  const getLatestFailedJob = useCallback(() => {
    return getJobs().find((job) => job.status === 'failed') || null;
  }, [getJobs]);
  const getSelectedRuns = useCallback(() => {
    return state.selectedRunIds.map(findRun).filter(Boolean);
  }, [state.selectedRunIds, findRun]);

  const findSweepDecisionRow = useCallback((entryId) => {
    for (const sweep of state.experimentsWorkspace.sweeps || []) {
      const row = (sweep.decisionRows || []).find((item) => item.entry_id === entryId);
      if (row) return { ...row, sweep };
    }
    return null;
  }, [state.experimentsWorkspace]);

  const decision = useMemo(() => ({
    getCandidateEntry: (storeOrRunId, maybeRunId) => {
      const store = maybeRunId ? storeOrRunId : state.candidatesStore;
      const runId = maybeRunId || storeOrRunId;
      return decisionStore.getCandidateEntry(store, runId);
    },
    getCandidateEntryResolved: (runId) =>
      decisionStore.getCandidateEntryResolved(state.candidatesStore, runId, findRun),
    getCandidateEntriesResolved: () =>
      decisionStore.getCandidateEntriesResolved(state.candidatesStore, findRun),
    buildMissingCandidateEntry: (runId) =>
      decisionStore.buildMissingCandidateEntry(runId, findRun),
    isCandidateRun: (runId) =>
      decisionStore.isCandidateRun(state.candidatesStore, runId),
    isShortlistedRun: (runId) =>
      decisionStore.isShortlistedRun(state.candidatesStore, runId),
    isBaselineRun: (runId) =>
      decisionStore.isBaselineRun(state.candidatesStore, runId),
    getDecisionCompareRunIds: () =>
      decisionStore.getDecisionCompareRunIds(
        state.candidatesStore,
        findRun,
        uniqueRunIds,
        CONFIG.maxCandidateCompare
      ),
    summarizeCandidateState: (storeOrRunId, maybeRunId) => {
      const store = maybeRunId ? storeOrRunId : state.candidatesStore;
      const runId = maybeRunId || storeOrRunId;
      return decisionStore.summarizeCandidateState(store, runId);
    },
  }), [state.candidatesStore, findRun]);

  const sweepDecision = useMemo(() => ({
    getEntriesResolved: (store, findLiveRow) =>
      sweepDecisionStore.getSweepDecisionEntriesResolved(store, findLiveRow),
    getEntry: (store, entryId) =>
      sweepDecisionStore.getSweepDecisionEntry(store, entryId),
    isTracked: (store, entryId) =>
      sweepDecisionStore.isTrackedSweepEntry(store, entryId),
    isShortlisted: (store, entryId) =>
      sweepDecisionStore.isShortlistedSweepEntry(store, entryId),
    isBaseline: (store, entryId) =>
      sweepDecisionStore.isBaselineSweepEntry(store, entryId),
    summarizeState: (store, entryId) =>
      sweepDecisionStore.summarizeSweepDecisionState(store, entryId),
  }), []);

  const getSweepDecisionEntriesForRun = useCallback((runId) => {
    return sweepDecisionStore
      .getSweepDecisionEntriesResolved(state.sweepDecisionStore, findSweepDecisionRow)
      .filter((entry) => entry.sweep_run_id === runId);
  }, [state.sweepDecisionStore, findSweepDecisionRow]);

  const getRunRelatedJobs = useCallback((runId) => {
    return getJobs().filter((job) => {
      const payload = job.payload || job.request || {};
      const params = payload.params || payload;
      return (
        job.run_id === runId ||
        job.linked_run_id === runId ||
        params.run_id === runId ||
        params.out_dir === runId
      );
    });
  }, [getJobs]);

  const loadRunDetail = useCallback(async (runId) => {
    const run = findRun(runId);
    if (!run?.path) throw new Error(`Run ${runId} has no accessible artifact path.`);
    let detail = {
      report: null,
      reportUrl: null,
      directoryEntries: [],
      directoryTruncated: false,
    };

    for (const artifact of CONFIG.detailArtifacts) {
      const localArtifactPath = joinProjectPath(run.path, artifact);
      const href = buildRunArtifactHref(run.path, artifact);
      const localReport = await readOptionalJson(localArtifactPath);
      if (localReport) {
        detail = { ...detail, report: localReport, reportUrl: href || localArtifactPath };
        break;
      }
      if (href) {
        const remoteReport = await requestOptionalJson(href);
        if (remoteReport) {
          detail = { ...detail, report: remoteReport, reportUrl: href };
          break;
        }
      }
    }

    try {
      const listing = await getBridge().listDirectory(run.path, 2);
      detail.directoryEntries = listing.entries || [];
      detail.directoryTruncated = Boolean(listing.truncated);
    } catch (_error) {
      // Directory listing is optional evidence, not a hard runtime dependency.
    }

    return detail;
  }, [findRun]);

  const upsertTab = useCallback((tab) => {
    setState((current) => {
      const tabs = current.tabs.some((item) => item.id === tab.id)
        ? current.tabs.map((item) => (item.id === tab.id ? { ...item, ...tab } : item))
        : [...current.tabs, tab];
      return { ...current, tabs, activeTabId: tab.id };
    });
  }, []);

  const openRunDetailTab = useCallback(async (runId, options = {}) => {
    if (!runId) return; // Guard: runId must be a non-empty string (#451)
    const run = findRun(runId);
    if (!run) return;
    const subview = options.subview || '';
    const tabId = `run:${runId}`;
    const title = subview === 'artifacts' ? `Artifacts: ${run.run_id}` : `Run ${run.run_id}`;
    upsertTab({
      id: tabId,
      kind: 'run',
      navKind: 'runs',
      title,
      runId,
      subview,
      status: 'loading',
      detail: null,
      error: null,
    });
    try {
      const detail = await loadRunDetail(runId);
      upsertTab({
        id: tabId,
        kind: 'run',
        navKind: 'runs',
        title,
        runId,
        subview,
        status: 'ready',
        detail,
        error: null,
      });
    } catch (error) {
      upsertTab({
        id: tabId,
        kind: 'run',
        navKind: 'runs',
        title,
        runId,
        subview,
        status: 'error',
        detail: null,
        error: error.message || String(error),
      });
    }
  }, [findRun, loadRunDetail, upsertTab]);

  const openCompareSelectionTab = useCallback((runIds, label = 'selected runs') => {
    const ids = uniqueRunIds(runIds || []).filter((runId) => findRun(runId));
    if (ids.length < 2) return;
    upsertTab({
      id: `compare:${ids.join('|')}`,
      kind: 'compare',
      navKind: 'compare',
      title: `Compare: ${label}`,
      runIds: ids,
      status: 'loading',
    });
  }, [findRun, upsertTab]);

  const refreshJobTab = useCallback(async (requestId, fallbackJob = null) => {
    if (!requestId) return;
    const job = findJob(requestId) || fallbackJob;
    if (!job) return;
    const tabId = `job:${requestId}`;

    try {
      const [stdoutText, stderrText] = await Promise.all([
        requestOptionalText(job.stdout_href),
        requestOptionalText(job.stderr_href),
      ]);
      upsertTab({
        id: tabId,
        kind: 'job',
        navKind: 'launch',
        title: `Job ${requestId}`,
        requestId,
        jobId: requestId,
        status: 'ready',
        job: findJob(requestId) || job,
        stdoutText,
        stderrText,
        error: null,
      });
    } catch (error) {
      upsertTab({
        id: tabId,
        kind: 'job',
        navKind: 'launch',
        title: `Job ${requestId}`,
        requestId,
        jobId: requestId,
        status: 'error',
        job,
        stdoutText: '',
        stderrText: '',
        error: error.message || 'Could not load job logs.',
      });
    }
  }, [findJob, upsertTab]);

  const openJobTab = useCallback(async (requestId) => {
    if (!requestId) return;
    const job = findJob(requestId);
    if (!job) return;
    const tabId = `job:${requestId}`;
    upsertTab({
      id: tabId,
      kind: 'job',
      navKind: 'launch',
      title: `Job ${requestId}`,
      requestId,
      jobId: requestId,
      status: 'loading',
      job,
      stdoutText: '',
      stderrText: '',
      error: null,
    });
    await refreshJobTab(requestId, job);
  }, [findJob, refreshJobTab, upsertTab]);

  /**
   * openTab — unified tab-open API.
   *
   * Preferred (object form):
   *   openTab({ kind: 'run', runId })
   *   openTab({ kind: 'compare', runIds: [...], label: '...' })
   *   openTab({ kind: 'job', requestId })
   *   openTab({ kind: 'system' })   // surface tabs need no extra payload
   *
   * Legacy positional shim (still accepted, will be removed in #455):
   *   openTab('run', runId)
   *   openTab('job', requestId)
   *   openTab('launch', title, href)
   *
   * 'shortlist-compare' is no longer a valid kind (#450).
   * Use openTab({ kind: 'compare', runIds: decision.getDecisionCompareRunIds() }) instead.
   */
  const openTab = useCallback((kindOrTab, arg, href) => {
    // Object form: openTab({ kind, ... })
    const isObj = kindOrTab !== null && typeof kindOrTab === 'object';
    const kind = isObj ? kindOrTab.kind : kindOrTab;

    if (kind === 'run') {
      const runId = isObj ? kindOrTab.runId : arg;
      if (!runId) return; // Guard: prevents run:undefined tabs (#451)
      openRunDetailTab(runId);
      return;
    }
    if (kind === 'artifacts') {
      const runId = isObj ? kindOrTab.runId : arg;
      if (!runId) return;
      openRunDetailTab(runId, { subview: 'artifacts' });
      return;
    }
    if (kind === 'compare') {
      // Object form carries explicit runIds; positional falls back to selectedRunIds.
      const runIds = isObj && Array.isArray(kindOrTab.runIds)
        ? kindOrTab.runIds
        : state.selectedRunIds;
      const label = (isObj && kindOrTab.label) || 'selected runs';
      openCompareSelectionTab(runIds, label);
      return;
    }
    if (kind === 'job') {
      const requestId = isObj ? kindOrTab.requestId : arg;
      if (!requestId) return;
      openJobTab(requestId);
      return;
    }

    // Surface tabs (no payload beyond optional title/href)
    const surfaceTabs = {
      system: { id: 'system', kind: 'system', navKind: 'system', title: 'System' },
      experiments: {
        id: 'experiments',
        kind: 'experiments',
        navKind: 'experiments',
        title: 'Experiments',
        selectedConfigPath: state.experimentsWorkspace.configs[0]?.path || null,
        selectedSweepId: state.experimentsWorkspace.sweeps[0]?.run_id || null,
      },
      launch: {
        id: 'launch',
        kind: 'launch',
        navKind: 'launch',
        title: (isObj ? kindOrTab.title : arg) || 'Launch',
        href: isObj ? kindOrTab.href : href,
      },
      hypothesis: {
        id: 'hypothesis',
        kind: 'hypothesis',
        navKind: 'hypothesis',
        title: 'Hypothesis Builder',
      },
      runs: createRunsTab(),
      candidates: {
        id: 'candidates',
        kind: 'candidates',
        navKind: 'candidates',
        title: 'Candidates',
      },
      paper: {
        id: 'paper-ops',
        kind: 'paper',
        navKind: 'paper-ops',
        title: 'Paper Ops',
      },
      'paper-ops': {
        id: 'paper-ops',
        kind: 'paper',
        navKind: 'paper-ops',
        title: 'Paper Ops',
      },
      assistant: {
        id: 'assistant',
        kind: 'assistant',
        navKind: 'assistant',
        title: 'Assistant',
      },
    };

    const tab = surfaceTabs[kind];
    if (tab) upsertTab(tab);
  }, [
    decision,
    openCompareSelectionTab,
    openJobTab,
    openRunDetailTab,
    state.experimentsWorkspace,
    state.selectedRunIds,
    upsertTab,
  ]);

  const closeTab = useCallback((tabId) => {
    setState((current) => {
      const tabs = current.tabs.filter((tab) => tab.id !== tabId);
      const activeTabId = current.activeTabId === tabId
        ? tabs[tabs.length - 1]?.id || null
        : current.activeTabId;
      return { ...current, tabs, activeTabId };
    });
  }, []);

  const setActiveTab = useCallback((tabId) => {
    setState((current) => {
      const directMatch = current.tabs.some((tab) => tab.id === tabId);
      if (directMatch) return { ...current, activeTabId: tabId };
      return current;
    });
  }, []);

  const toggleRunSelection = useCallback((runId) => {
    setState((current) => {
      const selected = current.selectedRunIds.includes(runId);
      const selectedRunIds = selected
        ? current.selectedRunIds.filter((item) => item !== runId)
        : current.selectedRunIds.length < 4
          ? [...current.selectedRunIds, runId]
          : current.selectedRunIds;
      return { ...current, selectedRunIds };
    });
  }, []);

  const saveCandidatesStore = useCallback(async (nextStore) => {
    const normalized = decisionStore.normalizeCandidatesStore(nextStore);
    setState((current) => ({
      ...current,
      candidatesStore: normalized,
    }));
    try {
      const persisted = decisionStore.normalizeCandidatesStore(
        await getBridge().saveCandidatesStore(normalized)
      );
      setState((current) => ({
        ...current,
        candidatesStore: persisted,
      }));
    } catch (_error) {
      // Keep optimistic local decision state if persistence is temporarily unavailable.
    }
  }, []);

  const toggleCandidate = useCallback(async (runId, forceValue = null) => {
    const existing = decisionStore.getCandidateEntry(state.candidatesStore, runId);
    const shouldExist = forceValue === null ? !existing : Boolean(forceValue);
    const entries = decisionStore
      .getCandidateEntries(state.candidatesStore)
      .filter((entry) => entry.run_id !== runId);
    if (shouldExist) entries.push(buildCandidateEntry(runId, existing));
    await saveCandidatesStore({
      ...state.candidatesStore,
      entries,
      baseline_run_id:
        shouldExist || state.candidatesStore.baseline_run_id !== runId
          ? state.candidatesStore.baseline_run_id
          : null,
      updated_at: new Date().toISOString(),
    });
  }, [saveCandidatesStore, state.candidatesStore]);

  const toggleShortlist = useCallback(async (runId) => {
    const existing = decisionStore.getCandidateEntry(state.candidatesStore, runId);
    const entries = decisionStore
      .getCandidateEntries(state.candidatesStore)
      .filter((entry) => entry.run_id !== runId);
    entries.push({
      ...buildCandidateEntry(runId, existing),
      shortlisted: !existing?.shortlisted,
    });
    await saveCandidatesStore({
      ...state.candidatesStore,
      entries,
      updated_at: new Date().toISOString(),
    });
  }, [saveCandidatesStore, state.candidatesStore]);

  const setBaseline = useCallback(async (runId) => {
    let entries = decisionStore.getCandidateEntries(state.candidatesStore);
    if (runId && !decisionStore.getCandidateEntry(state.candidatesStore, runId)) {
      entries = [...entries, buildCandidateEntry(runId)];
    }
    await saveCandidatesStore({
      ...state.candidatesStore,
      entries,
      baseline_run_id: runId || null,
      updated_at: new Date().toISOString(),
    });
  }, [saveCandidatesStore, state.candidatesStore]);

  const saveSweepStore = useCallback(async (nextStore) => {
    const normalized = sweepDecisionStore.normalizeSweepDecisionStore(nextStore);
    setState((current) => ({ ...current, sweepDecisionStore: normalized }));
    try {
      const persisted = sweepDecisionStore.normalizeSweepDecisionStore(
        await getBridge().saveSweepDecisionStore(normalized)
      );
      setState((current) => ({ ...current, sweepDecisionStore: persisted }));
    } catch (_error) {
      // Keep optimistic sweep decision state if persistence is temporarily unavailable.
    }
  }, []);

  const toggleSweepEntry = useCallback(async (row) => {
    const entryId = row?.entry_id;
    if (!entryId) return;
    const existing = sweepDecisionStore.getSweepDecisionEntry(state.sweepDecisionStore, entryId);
    const entries = sweepDecisionStore.getSweepDecisionEntries(state.sweepDecisionStore)
      .filter((e) => e.entry_id !== entryId);
    if (!existing) {
      entries.push({
        entry_id: entryId,
        sweep_run_id: row.sweep_run_id || row.sweep?.run_id || '',
        source: row.source || 'leaderboard',
        row_index: typeof row.row_index === 'number' ? row.row_index : 0,
        config_path: row.config_path || '',
        row_snapshot: row,
        shortlisted: false,
        note: '',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    }
    await saveSweepStore({ ...state.sweepDecisionStore, entries, updated_at: new Date().toISOString() });
  }, [saveSweepStore, state.sweepDecisionStore]);

  const toggleSweepShortlist = useCallback(async (entryId) => {
    const existing = sweepDecisionStore.getSweepDecisionEntry(state.sweepDecisionStore, entryId);
    if (!existing) return;
    const entries = sweepDecisionStore.getSweepDecisionEntries(state.sweepDecisionStore)
      .map((e) => e.entry_id === entryId
        ? { ...e, shortlisted: !e.shortlisted, updated_at: new Date().toISOString() }
        : e);
    await saveSweepStore({ ...state.sweepDecisionStore, entries, updated_at: new Date().toISOString() });
  }, [saveSweepStore, state.sweepDecisionStore]);

  const setSweepBaseline = useCallback(async (entryId) => {
    await saveSweepStore({
      ...state.sweepDecisionStore,
      baseline_entry_id: entryId || null,
      updated_at: new Date().toISOString(),
    });
  }, [saveSweepStore, state.sweepDecisionStore]);

  const refresh = useCallback(async (workspaceOverride = null) => {
    const workspace = workspaceOverride || await getBridge().getWorkspaceState();
    const [snapshotState, candidatesStore, sweepStore, experimentsWorkspace] =
      await Promise.all([
        loadSnapshot(workspace),
        getBridge().getCandidatesStore().then(decisionStore.normalizeCandidatesStore),
        getBridge().getSweepDecisionStore().then(sweepDecisionStore.normalizeSweepDecisionStore),
        loadExperimentsWorkspace(),
      ]);

    setState((current) => ({
      ...current,
      workspace,
      ...snapshotState,
      candidatesStore,
      sweepDecisionStore: sweepStore,
      experimentsWorkspace,
    }));
  }, []);

  useEffect(() => {
    let mounted = true;

    refresh().catch((error) => {
      if (!mounted) return;
      setState((current) => ({
        ...current,
        workspace: {
          ...current.workspace,
          status: 'error',
          error: error.message || String(error),
        },
        snapshotStatus: createSnapshotStatus('none', error),
      }));
    });

    const unsubscribe = getBridge().onWorkspaceState((workspace) => {
      if (!mounted) return;
      refresh(workspace).catch(() => {});
    });

    return () => {
      mounted = false;
      unsubscribe();
    };
  }, [refresh]);

  const contextState = useMemo(() => ({
    ...state,
    runs: getRuns(),
    launchControl: state.snapshot.launchControl,
    decisionStore: state.candidatesStore,
    decision,
    sweepDecision,
  }), [state, getRuns, decision, sweepDecision]);

  return useMemo(() => ({
    state: contextState,
    getRuns,
    getLatestRun,
    findRun,
    getSelectedRuns,
    getJobs,
    findJob,
    getLatestFailedJob,
    getRunRelatedJobs,
    getSweepDecisionEntriesForRun,
    findSweepDecisionRow,
    loadRunDetail,
    decision,
    openTab,
    openJobTab,
    refreshJobTab,
    closeTab,
    setActiveTab,
    toggleRunSelection,
    toggleCandidate,
    toggleShortlist,
    setBaseline,
    toggleSweepEntry,
    toggleSweepShortlist,
    setSweepBaseline,
    refresh,
  }), [
    contextState,
    getRuns,
    getLatestRun,
    findRun,
    getSelectedRuns,
    getJobs,
    findJob,
    getLatestFailedJob,
    getRunRelatedJobs,
    getSweepDecisionEntriesForRun,
    findSweepDecisionRow,
    loadRunDetail,
    decision,
    openTab,
    openJobTab,
    refreshJobTab,
    closeTab,
    setActiveTab,
    toggleRunSelection,
    toggleCandidate,
    toggleShortlist,
    setBaseline,
    toggleSweepEntry,
    toggleSweepShortlist,
    setSweepBaseline,
    refresh,
  ]);
}

export const QuantLabContextProvider = ({ value, children }) => (
  <QuantLabContext.Provider value={value}>{children}</QuantLabContext.Provider>
);
