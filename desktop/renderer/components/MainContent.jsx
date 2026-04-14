import React, { useEffect, useRef } from 'react';

/**
 * MainContent - Main content area that:
 * - Mounts React-based surfaces
 * - Provides container for legacy surface HTML
 * - Manages surface tab context
 * 
 * This is the focused surface area where surfaces are rendered.
 * It does NOT migrate existing surfaces yet, but provides the foundation
 * for gradual migration from legacy to React.
 */
export default function MainContent({ currentSurface, onNavigate }) {
  const contentRef = useRef(null);
  const legacyContainerRef = useRef(null);

  useEffect(() => {
    // When surface changes, we would dispatch to the legacy app or React renderers
    // For now, we provide hooks for the legacy system to use
    console.log(`MainContent: Surface changed to ${currentSurface}`);
    
    // If there's a global legacy app handler, we can call it here
    if (window.__quantlab && window.__quantlab.onSurfaceChange) {
      window.__quantlab.onSurfaceChange(currentSurface);
    }
  }, [currentSurface]);

  // Expose a ref so legacy code can mount content
  useEffect(() => {
    if (window.__quantlab) {
      window.__quantlab.legacyContentContainer = legacyContainerRef.current;
      window.__quantlab.reactShell = { currentSurface, onNavigate };
    }
  }, [currentSurface, onNavigate]);

  return (
    <main className="main-content">
      <div className="content-tabs">
        <div className="tabs-header">
          <div className="tab-header-label">Active surface</div>
        </div>

        {/* Legacy surface container - existing surfaces render here */}
        <div 
          ref={legacyContainerRef}
          className="surface-container"
          data-surface={currentSurface}
        >
          {/* Legacy content will be mounted here by app.js */}
          <div id="legacy-render-root">
            {/* Placeholder until legacy content is mounted */}
            <div className="surface-placeholder">
              <p>Loading {formatSurfaceLabel(currentSurface)}...</p>
            </div>
          </div>
        </div>
      </div>

      {/* Support lane - contextual information  */}
      <aside className="support-lane">
        <div className="support-header">
          <div className="support-label">Context</div>
        </div>
        <div className="support-content">
          <p className="support-placeholder">
            Surface-specific context and controls appear here.
          </p>
        </div>
      </aside>
    </main>
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
