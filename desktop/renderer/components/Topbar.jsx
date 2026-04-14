import React from 'react';

/**
 * Topbar - Top navigation bar with:
 * - Runtime status indicator
 * - Version display
 * - Sidebar toggle
 * 
 * This is the minimal topbar for the new shell frame.
 * It provides visibility into system state without replacing legacy surfaces.
 */
export default function Topbar({ currentSurface, onToggleSidebar, isSidebarCollapsed }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <button 
          className="topbar-toggle" 
          onClick={onToggleSidebar}
          aria-label={isSidebarCollapsed ? "Open sidebar" : "Close sidebar"}
          title={isSidebarCollapsed ? "Open sidebar" : "Close sidebar"}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      <div className="topbar-center">
        <h1 className="topbar-title">QuantLab Desktop</h1>
      </div>

      <div className="topbar-right">
        <div className="topbar-status">
          <span className="topbar-surface-label">{formatSurfaceLabel(currentSurface)}</span>
          <div className="topbar-runtime-indicator">
            <span className="indicator-dot online" aria-hidden="true"></span>
            <span className="indicator-label">Ready</span>
          </div>
        </div>
      </div>
    </header>
  );
}

/**
 * Format surface name for display
 * @param {string} surface
 * @returns {string}
 */
function formatSurfaceLabel(surface) {
  const labels = {
    'system': 'System',
    'experiments': 'Experiments',
    'launch': 'Launch',
    'runs': 'Runs',
    'candidates': 'Candidates',
    'compare': 'Compare',
    'paper-ops': 'Paper Ops',
    'assistant': 'Assistant',
  };
  return labels[surface] || surface;
}
