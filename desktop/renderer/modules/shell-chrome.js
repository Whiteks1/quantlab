export const SHELL_COPY = {
  topbarEyebrow: "QuantLab Research workstation",
  assistantWelcome:
    "QuantLab Desktop is now workstation-first.\n\nUse the assistant as support when needed:\n- open system\n- open experiments\n- launch run ticker ETH-USD start 2023-01-01 end 2024-01-01\n- open latest run\n- compare selected\n- show artifacts\n- open latest failed launch\n- explain latest failure\n- ask stepbit explain the latest failed launch",
  assistantHelp:
    "This shell now supports real backend-backed actions. Try:\n- open system\n- open experiments\n- open sweep handoff\n- launch run ticker ETH-USD start 2023-01-01 end 2024-01-01\n- launch sweep config configs/experiments/eth_2023_grid.yaml\n- open candidates\n- mark candidate <run_id>\n- mark baseline <run_id>\n- open latest run\n- compare selected\n- show artifacts\n- open latest failed launch\n- explain latest failure\n- ask stepbit explain the latest failed launch",
  emptyWorksurface:
    "No focused work surface is open yet.\n\nUse the sidebar, workflow panel, or assistant support to open runs, compare candidates, inspect artifacts, or review runtime state.",
  paletteEmptyState: "No matching action. Try shortlist, baseline, compare, or paper.",
  defaultTopbarTitle: "Workstation",
  defaultTopbarSurface: "No active surface",
  defaultTopbarRuntime: "Runtime waiting",
  defaultTopbarServer: "Bootstrap pending",
  defaultLaunchFeedback: "Use deterministic inputs or the assistant when needed.",
};

export const NAV_ACTION_BY_KIND = {
  assistant: "open-assistant",
  system: "open-system",
  experiments: "open-experiments",
  launch: "open-launch",
  runs: "open-runs",
  candidates: "open-candidates",
  compare: "open-compare",
  ops: "open-ops",
};

export const PALETTE_ACTION_SPECS = [
  {
    id: "assistant",
    label: "Focus Assistant",
    description: "Move focus to the support assistant without leaving the active work surface.",
    handler: "focusAssistant",
  },
  {
    id: "system",
    label: "Open System",
    description: "Open runtime diagnostics, inventory, and launch visibility.",
    handler: "openSystemTab",
  },
  {
    id: "experiments",
    label: "Open Experiments",
    description: "Open the native experiments and sweeps workspace.",
    handler: "openExperimentsTab",
  },
  {
    id: "sweep-handoff",
    label: "Open Sweep Handoff",
    description: "Open the local sweep decision handoff compare.",
    handler: "openSweepDecisionTab",
  },
  {
    id: "launch",
    label: "Open Launch (browser)",
    description: "Open the browser-backed Launch surface (transitional path).",
    handler: "openLaunchTab",
  },
  {
    id: "runs",
    label: "Open Runs",
    description: "Open the native run explorer.",
    handler: "openRunsNativeTab",
  },
  {
    id: "candidates",
    label: "Open Candidates",
    description: "Open the shortlist and baseline surface.",
    handler: "openCandidatesTab",
  },
  {
    id: "compare",
    label: "Open Compare",
    description: "Open a compare tab from selected runs.",
    handler: "openCompareSelectionTab",
  },
  {
    id: "shortlist-compare",
    label: "Open Shortlist Compare",
    description: "Compare the current shortlist or baseline set.",
    handler: "openShortlistCompareTab",
  },
  {
    id: "baseline-run",
    label: "Open Baseline Run",
    description: "Open the current baseline run workspace.",
    handler: "openBaselineRunTab",
  },
  {
    id: "ops",
    label: "Open Paper Ops",
    description: "Open the native operational surface.",
    handler: "openPaperOpsTab",
  },
  {
    id: "latest-run",
    label: "Open Latest Run",
    description: "Open the latest run detail.",
    handler: "openLatestRunTab",
  },
  {
    id: "latest-failed",
    label: "Open Latest Failed Launch",
    description: "Review the most recent failed launch job.",
    handler: "openLatestFailedLaunchTab",
  },
  {
    id: "explain-failure",
    label: "Explain Latest Failure",
    description: "Summarize the latest failed launch from stderr and job state.",
    handler: "explainLatestFailureInChat",
  },
  {
    id: "stepbit-failure",
    label: "Ask Stepbit About Failure",
    description: "Use the Stepbit-backed adapter to inspect the latest failed launch.",
    handler: "askStepbitAboutLatestFailure",
  },
  {
    id: "artifacts",
    label: "Show Artifacts",
    description: "Open artifacts for the selected or latest run.",
    handler: "openArtifactsForPreferredRun",
  },
  {
    id: "runtime",
    label: "Show Runtime Status",
    description: "Summarize runtime health through the assistant support lane.",
    handler: "summarizeRuntimeInChat",
  },
  {
    id: "runs-legacy",
    label: "Open Runs (Legacy) — browser fallback",
    description: "Browser-based run explorer. Use only when native Runs surface is unavailable.",
    handler: "openLegacyRunsTab",
    legacy: true,
  },
];
