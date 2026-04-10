// @ts-check

/**
 * @param {{
 *   fs: typeof import("fs"),
 *   fsp: typeof import("fs/promises"),
 *   path: typeof import("path"),
 *   projectRoot: string,
 *   candidatesStorePath: string,
 *   sweepDecisionStorePath: string,
 *   workspaceStorePath: string,
 *   maxDirectoryEntries: number,
 * }} options
 */
function createLocalStoreService({
  fs,
  fsp,
  path,
  projectRoot,
  candidatesStorePath,
  sweepDecisionStorePath,
  workspaceStorePath,
  maxDirectoryEntries,
}) {
  function defaultCandidatesStore() {
    return {
      version: 1,
      updated_at: null,
      baseline_run_id: null,
      entries: [],
    };
  }

  function normalizeCandidateEntry(entry) {
    if (!entry || typeof entry !== "object" || !entry.run_id) return null;
    const now = new Date().toISOString();
    return {
      run_id: String(entry.run_id),
      note: typeof entry.note === "string" ? entry.note : "",
      shortlisted: Boolean(entry.shortlisted),
      created_at: entry.created_at || now,
      updated_at: entry.updated_at || now,
    };
  }

  function normalizeCandidatesStore(store) {
    const fallback = defaultCandidatesStore();
    if (!store || typeof store !== "object") return fallback;
    const entries = Array.isArray(store.entries)
      ? store.entries.map(normalizeCandidateEntry).filter(Boolean)
      : [];
    return {
      version: 1,
      updated_at: store.updated_at || null,
      baseline_run_id: store.baseline_run_id ? String(store.baseline_run_id) : null,
      entries,
    };
  }

  function defaultSweepDecisionStore() {
    return {
      version: 1,
      updated_at: null,
      baseline_entry_id: null,
      entries: [],
    };
  }

  function normalizeSweepDecisionEntry(entry) {
    if (!entry || typeof entry !== "object" || !entry.entry_id || !entry.sweep_run_id) return null;
    const now = new Date().toISOString();
    return {
      entry_id: String(entry.entry_id),
      sweep_run_id: String(entry.sweep_run_id),
      source: typeof entry.source === "string" ? entry.source : "leaderboard",
      row_index: Number.isFinite(Number(entry.row_index)) ? Number(entry.row_index) : 0,
      note: typeof entry.note === "string" ? entry.note : "",
      shortlisted: Boolean(entry.shortlisted),
      config_path: typeof entry.config_path === "string" ? entry.config_path : "",
      row_snapshot: entry.row_snapshot && typeof entry.row_snapshot === "object" ? entry.row_snapshot : null,
      created_at: entry.created_at || now,
      updated_at: entry.updated_at || now,
    };
  }

  function normalizeSweepDecisionStore(store) {
    const fallback = defaultSweepDecisionStore();
    if (!store || typeof store !== "object") return fallback;
    const entries = Array.isArray(store.entries)
      ? store.entries.map(normalizeSweepDecisionEntry).filter(Boolean)
      : [];
    return {
      version: 1,
      updated_at: store.updated_at || null,
      baseline_entry_id: store.baseline_entry_id ? String(store.baseline_entry_id) : null,
      entries,
    };
  }

  function defaultShellWorkspaceStore() {
    return {
      version: 1,
      updated_at: null,
      active_tab_id: null,
      selected_run_ids: [],
      tabs: [],
      launch_form: {
        command: "run",
        ticker: "",
        start: "",
        end: "",
        interval: "",
        cash: "",
        paper: false,
        config_path: "",
        out_dir: "",
      },
    };
  }

  function normalizeShellTab(tab) {
    if (!tab || typeof tab !== "object" || typeof tab.id !== "string" || typeof tab.kind !== "string") return null;
    const base = {
      id: String(tab.id),
      kind: String(tab.kind),
      navKind: typeof tab.navKind === "string" ? tab.navKind : "",
      title: typeof tab.title === "string" ? tab.title : "",
    };

    if (base.kind === "iframe") {
      if (typeof tab.url !== "string" || !tab.url) return null;
      return { ...base, url: tab.url };
    }

    if (base.kind === "run") {
      if (!tab.runId || !tab.mode) return null;
      return {
        ...base,
        runId: String(tab.runId),
        mode: String(tab.mode),
      };
    }

    if (base.kind === "artifacts") {
      if (!tab.runId) return null;
      return {
        ...base,
        runId: String(tab.runId),
      };
    }

    if (base.kind === "compare") {
      return {
        ...base,
        compareRunIds: Array.isArray(tab.compareRunIds) ? tab.compareRunIds.map((value) => String(value)) : [],
      };
    }

    if (base.kind === "job") {
      if (!tab.jobId) return null;
      return {
        ...base,
        jobId: String(tab.jobId),
      };
    }

    if (base.kind === "experiments") {
      return {
        ...base,
        selectedConfigPath: typeof tab.selectedConfigPath === "string" ? tab.selectedConfigPath : "",
        selectedSweepId: typeof tab.selectedSweepId === "string" ? tab.selectedSweepId : "",
      };
    }

    if (base.kind === "sweep-decision") {
      return {
        ...base,
        viewMode: typeof tab.viewMode === "string" ? tab.viewMode : "tracked",
      };
    }

    return base;
  }

  function normalizeShellWorkspaceStore(store) {
    const fallback = defaultShellWorkspaceStore();
    if (!store || typeof store !== "object") return fallback;
    const tabs = Array.isArray(store.tabs)
      ? store.tabs.map(normalizeShellTab).filter(Boolean)
      : [];
    const launchForm = store.launch_form && typeof store.launch_form === "object"
      ? {
          command: typeof store.launch_form.command === "string" ? store.launch_form.command : "run",
          ticker: typeof store.launch_form.ticker === "string" ? store.launch_form.ticker : "",
          start: typeof store.launch_form.start === "string" ? store.launch_form.start : "",
          end: typeof store.launch_form.end === "string" ? store.launch_form.end : "",
          interval: typeof store.launch_form.interval === "string" ? store.launch_form.interval : "",
          cash: typeof store.launch_form.cash === "string" ? store.launch_form.cash : "",
          paper: Boolean(store.launch_form.paper),
          config_path: typeof store.launch_form.config_path === "string" ? store.launch_form.config_path : "",
          out_dir: typeof store.launch_form.out_dir === "string" ? store.launch_form.out_dir : "",
        }
      : fallback.launch_form;

    return {
      version: 1,
      updated_at: store.updated_at || null,
      active_tab_id: typeof store.active_tab_id === "string" ? store.active_tab_id : null,
      selected_run_ids: Array.isArray(store.selected_run_ids)
        ? store.selected_run_ids.map((value) => String(value))
        : [],
      tabs,
      launch_form: launchForm,
    };
  }

  function assertPathInsideProject(targetPath) {
    const resolvedProjectRoot = path.resolve(projectRoot);
    const rawTarget = String(targetPath || "").trim();
    const resolvedTarget = path.isAbsolute(rawTarget)
      ? path.resolve(rawTarget)
      : path.resolve(projectRoot, rawTarget);
    const relative = path.relative(resolvedProjectRoot, resolvedTarget);
    if (!resolvedTarget || relative.startsWith("..") || (path.isAbsolute(relative) && relative === resolvedTarget)) {
      throw new Error("Requested path is outside the QuantLab workspace.");
    }
    return resolvedTarget;
  }

  async function readCandidatesStore() {
    try {
      const raw = await fsp.readFile(candidatesStorePath, "utf8");
      return normalizeCandidatesStore(JSON.parse(raw));
    } catch (error) {
      if (error && error.code === "ENOENT") return defaultCandidatesStore();
      throw error;
    }
  }

  async function writeCandidatesStore(store) {
    const normalized = normalizeCandidatesStore(store);
    normalized.updated_at = new Date().toISOString();
    await fsp.mkdir(path.dirname(candidatesStorePath), { recursive: true });
    await fsp.writeFile(candidatesStorePath, `${JSON.stringify(normalized, null, 2)}\n`, "utf8");
    return normalized;
  }

  async function readSweepDecisionStore() {
    try {
      const raw = await fsp.readFile(sweepDecisionStorePath, "utf8");
      return normalizeSweepDecisionStore(JSON.parse(raw));
    } catch (error) {
      if (error && error.code === "ENOENT") return defaultSweepDecisionStore();
      throw error;
    }
  }

  async function writeSweepDecisionStore(store) {
    const normalized = normalizeSweepDecisionStore(store);
    normalized.updated_at = new Date().toISOString();
    await fsp.mkdir(path.dirname(sweepDecisionStorePath), { recursive: true });
    await fsp.writeFile(sweepDecisionStorePath, `${JSON.stringify(normalized, null, 2)}\n`, "utf8");
    return normalized;
  }

  async function readShellWorkspaceStore() {
    try {
      const raw = await fsp.readFile(workspaceStorePath, "utf8");
      return normalizeShellWorkspaceStore(JSON.parse(raw));
    } catch (error) {
      if (error && error.code === "ENOENT") return defaultShellWorkspaceStore();
      throw error;
    }
  }

  async function writeShellWorkspaceStore(store) {
    const normalized = normalizeShellWorkspaceStore(store);
    normalized.updated_at = new Date().toISOString();
    await fsp.mkdir(path.dirname(workspaceStorePath), { recursive: true });
    await fsp.writeFile(workspaceStorePath, `${JSON.stringify(normalized, null, 2)}\n`, "utf8");
    return normalized;
  }

  async function listDirectoryEntries(targetPath, maxDepth = 2) {
    const rootPath = assertPathInsideProject(targetPath);
    /** @type {Array<{ path: string, kind: string, size: number, depth: number, mtimeMs: number }>} */
    const entries = [];

    async function walk(currentPath, depth) {
      if (entries.length >= maxDirectoryEntries) return;
      const dirEntries = await fsp.readdir(currentPath, { withFileTypes: true });
      for (const dirEntry of dirEntries) {
        if (entries.length >= maxDirectoryEntries) break;
        const resolved = path.join(currentPath, dirEntry.name);
        const stat = await fsp.stat(resolved);
        const relativePath = path.relative(projectRoot, resolved).replace(/\\/g, "/");
        entries.push({
          path: relativePath,
          kind: dirEntry.isDirectory() ? "directory" : "file",
          size: stat.size,
          depth,
          mtimeMs: stat.mtimeMs,
        });
        if (dirEntry.isDirectory() && depth < maxDepth) {
          await walk(resolved, depth + 1);
        }
      }
    }

    await walk(rootPath, 0);
    return entries;
  }

  async function readProjectText(targetPath) {
    const safePath = assertPathInsideProject(targetPath);
    return fsp.readFile(safePath, "utf8");
  }

  async function readProjectJson(targetPath) {
    const safePath = assertPathInsideProject(targetPath);
    return readJsonFile(safePath);
  }

  async function readJsonFile(targetPath) {
    const raw = await fsp.readFile(targetPath, "utf8");
    try {
      return JSON.parse(raw);
    } catch (error) {
      throw new Error(`Failed to parse JSON at ${path.relative(projectRoot, targetPath)}: ${error.message}`);
    }
  }

  return {
    assertPathInsideProject,
    readCandidatesStore,
    writeCandidatesStore,
    readSweepDecisionStore,
    writeSweepDecisionStore,
    readShellWorkspaceStore,
    writeShellWorkspaceStore,
    listDirectoryEntries,
    readProjectText,
    readProjectJson,
    readJsonFile,
  };
}

module.exports = { createLocalStoreService };
