/**
 * QuantLab Research Dashboard - Core Application Logic
 * Phase 1: Run Index MVP
 */

const CONFIG = {
    registryPath: '/outputs/runs/runs_index.json',
    refreshInterval: 30000 // 30s
};

let state = {
    runs: [],
    filteredRuns: [],
    sortField: 'created_at',
    sortDir: 'desc',
    filterMode: 'all',
    searchQuery: '',
    isLoading: false,
    currentView: 'runs'
};

// --- DOM References ---
const elements = {
    runsBody: document.getElementById('runs-body'),
    totalRuns: document.getElementById('stats-total-runs'),
    activeSessions: document.getElementById('stats-active-sessions'),
    searchInput: document.getElementById('run-search'),
    modeFilter: document.getElementById('filter-mode'),
    refreshBtn: document.getElementById('refresh-data'),
    breadcrumb: document.getElementById('breadcrumb'),
    views: {
        runs: document.getElementById('run-index-view'),
        detail: document.getElementById('run-detail-view')
    },
    navItems: {
        runs: document.getElementById('nav-runs'),
        compare: document.getElementById('nav-compare')
    }
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    init();
});

function init() {
    // Event Listeners
    elements.refreshBtn.addEventListener('click', fetchData);
    elements.searchInput.addEventListener('input', handleSearch);
    elements.modeFilter.addEventListener('change', handleModeFilter);
    
    // Table Sorting
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', () => handleSort(th.dataset.sort));
    });

    // Simple Router
    window.addEventListener('hashchange', handleRouting);
    handleRouting();

    // Initial Load
    fetchData();
}

// --- Data Fetching ---
async function fetchData() {
    state.isLoading = true;
    renderTable(); // Show loading state

    try {
        const response = await fetch(CONFIG.registryPath);
        if (!response.ok) throw new Error(`Artifact not found: ${response.status}`);
        
        const data = await response.json();
        state.runs = data.runs || [];
        
        // Basic Post-processing: ensure numbers are numbers
        state.runs.forEach(run => {
            run.total_return = run.total_return !== null ? parseFloat(run.total_return) : null;
            run.sharpe_simple = run.sharpe_simple !== null ? parseFloat(run.sharpe_simple) : null;
            run.max_drawdown = run.max_drawdown !== null ? parseFloat(run.max_drawdown) : null;
        });

        notify('Registry synchronized', 'success');
    } catch (err) {
        console.error('Fetch error:', err);
        notify(`Fetch failed: ${err.message}`, 'error');
        state.runs = [];
    } finally {
        state.isLoading = false;
        applyFilters();
    }
}

// --- Logic: Filtering & Sorting ---
function applyFilters() {
    let filtered = [...state.runs];

    // Search filter (Ticker or Run ID)
    if (state.searchQuery) {
        const q = state.searchQuery.toLowerCase();
        filtered = filtered.filter(r => 
            (r.ticker && r.ticker.toLowerCase().includes(q)) || 
            (r.run_id && r.run_id.toLowerCase().includes(q))
        );
    }

    // Mode filter
    if (state.filterMode !== 'all') {
        filtered = filtered.filter(r => r.mode === state.filterMode);
    }

    // Sort
    filtered.sort((a, b) => {
        let vA = a[state.sortField];
        let vB = b[state.sortField];

        // Handle nulls
        if (vA === null || vA === undefined) return 1;
        if (vB === null || vB === undefined) return -1;

        if (vA < vB) return state.sortDir === 'asc' ? -1 : 1;
        if (vA > vB) return state.sortDir === 'asc' ? 1 : -1;
        return 0;
    });

    state.filteredRuns = filtered;
    updateStats();
    renderTable();
}

function handleSearch(e) {
    state.searchQuery = e.target.value;
    applyFilters();
}

function handleModeFilter(e) {
    state.filterMode = e.target.value;
    applyFilters();
}

function handleSort(field) {
    if (state.sortField === field) {
        state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
    } else {
        state.sortField = field;
        state.sortDir = 'desc'; // Default to desc for new fields
    }
    applyFilters();
}

// --- Logic: Routing ---
function handleRouting() {
    const hash = window.location.hash || '#/';
    
    // Reset views
    Object.values(elements.views).forEach(v => v.classList.remove('active'));
    Object.values(elements.navItems).forEach(v => v.classList.remove('active'));

    if (hash === '#/' || hash === '') {
        elements.views.runs.classList.add('active');
        elements.navItems.runs.classList.add('active');
        elements.breadcrumb.textContent = 'Run Registry';
    } else if (hash.startsWith('#/run/')) {
        const runId = hash.split('/')[2];
        elements.views.detail.classList.add('active');
        elements.breadcrumb.textContent = `Run Detail: ${runId}`;
        // Phase 2: Load detail data
    } else {
        // Fallback to registry
        window.location.hash = '#/';
    }
}

// --- Rendering ---
function renderTable() {
    if (state.isLoading && state.runs.length === 0) {
        elements.runsBody.innerHTML = `
            <tr>
                <td colspan="8" class="loading-state">
                    <div class="spinner"></div>
                    Accessing QuantLab artifacts...
                </td>
            </tr>
        `;
        return;
    }

    if (state.filteredRuns.length === 0) {
        elements.runsBody.innerHTML = `
            <tr>
                <td colspan="8" class="loading-state">
                    No runs matched your filters.
                </td>
            </tr>
        `;
        return;
    }

    elements.runsBody.innerHTML = state.filteredRuns.map(run => {
        const dateStr = run.created_at ? new Date(run.created_at).toLocaleString() : 'N/A';
        const retCls = run.total_return >= 0 ? 'text-success' : 'text-danger';
        const modeBadge = getModeBadge(run.mode);
        
        return `
            <tr>
                <td class="font-mono">${run.run_id || 'unnamed'}</td>
                <td><span class="badge ${modeBadge}">${run.mode || 'unknown'}</span></td>
                <td><strong>${run.ticker || 'N/A'}</strong></td>
                <td class="${retCls}">${formatPct(run.total_return)}</td>
                <td>${formatNum(run.sharpe_simple)}</td>
                <td class="text-danger">${formatPct(run.max_drawdown)}</td>
                <td class="text-secondary">${dateStr}</td>
                <td>
                    <button class="btn-icon" onclick="location.hash='#/run/${run.run_id}'" title="View Details">
                        <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                    </button>
                    <button class="btn-icon" title="Open Folder (Local)" onclick="console.log('Path: ${run.path}')">
                        <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function updateStats() {
    elements.totalRuns.textContent = state.runs.length;
    // Mocking active sessions as runs from last 24h
    const dayAgo = new Date();
    dayAgo.setDate(dayAgo.getDate() - 1);
    const active = state.runs.filter(r => new Date(r.created_at) > dayAgo).length;
    elements.activeSessions.textContent = active;
}

// --- Helpers ---
function formatPct(val) {
    if (val === null || val === undefined) return '-';
    return (val * 100).toFixed(2) + '%';
}

function formatNum(val) {
    if (val === null || val === undefined) return '-';
    return val.toFixed(2);
}

function getModeBadge(mode) {
    switch(mode) {
        case 'run': return 'badge-blue';
        case 'sweep': return 'badge-purple';
        case 'forward': return 'badge-green';
        default: return '';
    }
}

function notify(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Future: implement toast UI
}

// Expose simple event handlers to global scope for row buttons
window.getModeBadge = getModeBadge;
