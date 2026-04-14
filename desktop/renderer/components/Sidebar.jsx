import React from 'react';

/**
 * Sidebar - Left navigation sidebar with:
 * - Brand mark and title
 * - Navigation items (System, Experiments, Launch, Runs, etc.)
 * - Current principle panel
 * - Runtime status
 * 
 * Maps navigation actions to surface routing.
 */
export default function Sidebar({ currentSurface, onNavigate, isCollapsed }) {
  const navItems = [
    { id: 'system', label: 'System', icon: 'settings' },
    { id: 'experiments', label: 'Experiments', icon: 'beaker' },
    { id: 'launch', label: 'Launch', icon: 'play' },
    { id: 'runs', label: 'Runs', icon: 'list' },
    { id: 'candidates', label: 'Candidates', icon: 'trophy' },
    { id: 'compare', label: 'Compare', icon: 'scale' },
    { id: 'paper-ops', label: 'Paper Ops', icon: 'document' },
    { id: 'assistant', label: 'Assistant', icon: 'sparkles' },
  ];

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      {!isCollapsed && (
        <>
          {/* Brand Section */}
          <div className="sidebar-brand">
            <div className="brand-mark" aria-hidden="true">
              <span className="brand-mark-ring"></span>
              <span className="brand-mark-tail"></span>
              <span className="brand-mark-grid">
                <span></span>
                <span></span>
                <span></span>
                <span></span>
              </span>
              <span className="brand-mark-core"></span>
            </div>
            <div>
              <div className="brand-title">QuantLab Desktop</div>
              <div className="brand-subtitle">Research workstation</div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="sidebar-nav">
            {navItems.map((item) => (
              <button
                key={item.id}
                className={`nav-item ${currentSurface === item.id ? 'is-active' : ''}`}
                onClick={() => onNavigate(item.id)}
                title={item.label}
              >
                <span className="nav-icon">{item.label.charAt(0)}</span>
                <span className="nav-label">{item.label}</span>
              </button>
            ))}
          </nav>

          {/* Support Panels */}
          <div className="sidebar-panels">
            <section className="sidebar-panel">
              <div className="panel-label">Current principle</div>
              <p>One shell, one runtime strip, one place to launch, inspect, compare, and decide.</p>
            </section>

            <section className="sidebar-panel">
              <div className="panel-label">Runtime</div>
              <div className="runtime-chip">
                <span className="chip-indicator">●</span>
                <span className="chip-text">Ready</span>
              </div>
            </section>
          </div>
        </>
      )}
    </aside>
  );
}
