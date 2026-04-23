/**
 * Tab discriminated union for the QuantLab Desktop shell.
 *
 * Every surface in MainContent must correspond to one of these kinds.
 * Use `tab.kind` as the discriminant — never positional strings.
 *
 * Call sites should use `openTab(tab: Tab)` (object form).
 * The legacy positional `openTab(kind, arg, href)` is a temporary shim
 * that will be removed once all call sites are migrated (#450, #455).
 */

export type TabKind =
  | 'runs'
  | 'run'
  | 'artifacts'
  | 'compare'
  | 'candidates'
  | 'system'
  | 'experiments'
  | 'paper'
  | 'job'
  | 'assistant'
  | 'launch'
  | 'hypothesis';

// ── Surface tabs (singleton, no payload) ────────────────────────────────────

export type RunsTab = {
  kind: 'runs';
  id: 'runs-native';
  navKind: 'runs';
  title: string;
};

export type CandidatesTab = {
  kind: 'candidates';
  id: 'candidates';
  navKind: 'candidates';
  title: string;
};

export type SystemTab = {
  kind: 'system';
  id: 'system';
  navKind: 'system';
  title: string;
};

export type ExperimentsTab = {
  kind: 'experiments';
  id: 'experiments';
  navKind: 'experiments';
  title: string;
  selectedConfigPath: string | null;
  selectedSweepId: string | null;
};

export type PaperTab = {
  kind: 'paper';
  id: 'paper-ops';
  navKind: 'paper-ops';
  title: string;
};

export type AssistantTab = {
  kind: 'assistant';
  id: 'assistant';
  navKind: 'assistant';
  title: string;
};

export type LaunchTab = {
  kind: 'launch';
  id: 'launch';
  navKind: 'launch';
  title: string;
  href?: string;
};

export type HypothesisTab = {
  kind: 'hypothesis';
  id: 'hypothesis';
  navKind: 'hypothesis';
  title: string;
};

// ── Payload tabs (carry run/job/compare IDs) ─────────────────────────────────

export type RunTab = {
  kind: 'run';
  id: string;            // `run:${runId}`
  navKind: 'runs';
  title: string;
  runId: string;
  subview?: string;
  status: 'loading' | 'ready' | 'error';
  detail: unknown | null;
  error: string | null;
};

export type ArtifactsTab = {
  kind: 'artifacts';
  id: string;            // `run:${runId}` (same pane, different subview)
  navKind: 'runs';
  title: string;
  runId: string;
  subview: 'artifacts';
  status: 'loading' | 'ready' | 'error';
  detail: unknown | null;
  error: string | null;
};

export type CompareTab = {
  kind: 'compare';
  id: string;            // `compare:${runIds.join('|')}`
  navKind: 'compare';
  title: string;
  runIds: string[];
  status: 'loading' | 'ready';
  rankMetric?: string;
  detailMap?: Record<string, unknown>;
  /** Internal label passed to openCompareSelectionTab */
  label?: string;
};

export type JobTab = {
  kind: 'job';
  id: string;            // `job:${requestId}`
  navKind: 'launch';
  title: string;
  requestId: string;
  jobId: string;
  status: 'loading' | 'ready' | 'error';
  job: unknown | null;
  stdoutText: string;
  stderrText: string;
  error: string | null;
};

// ── Union ────────────────────────────────────────────────────────────────────

export type Tab =
  | RunsTab
  | RunTab
  | ArtifactsTab
  | CompareTab
  | CandidatesTab
  | SystemTab
  | ExperimentsTab
  | PaperTab
  | JobTab
  | AssistantTab
  | LaunchTab
  | HypothesisTab;

/** Narrow a Tab to one with a specific kind. */
export type TabOfKind<K extends TabKind> = Extract<Tab, { kind: K }>;
