// @ts-check

/**
 * app.js - React entry point for the QuantLab Desktop shell
 * 
 * This is the new React-based entry point (Issue #352) that:
 * - Mounts the React shell frame (Topbar, Sidebar, MainContent)
 * - Provides hooks for legacy surface rendering
 * - Preserves existing QuantLab Desktop behavior during transition
 * 
 * The legacy app logic is preserved in app-legacy.js and integrated
 * as needed through the legacy surface mounting system.
 */

import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './components/App.jsx';

// Global namespace for QuantLab Desktop
window.__quantlab = window.__quantlab || {};

/**
 * Initialize the React shell frame
 */
function initializeReactShell() {
  const rootElement = document.getElementById('react-root');
  
  if (!rootElement) {
    console.error('[QuantLab React] Root element not found');
    return false;
  }

  try {
    const root = createRoot(rootElement);
    root.render(React.createElement(App));
    console.log('[QuantLab React] Shell initialized successfully');
    return true;
  } catch (error) {
    console.error('[QuantLab React] Failed to initialize:', error);
    rootElement.innerHTML = '<div style="padding: 20px; background: #fee; color: #c33; font-family: monospace;">Failed to initialize QuantLab Desktop shell.</div>';
    return false;
  }
}

/**
 * Bridge for legacy surface rendering
 * 
 * Legacy surfaces can use window.__quantlab.renderLegacySurface(content)
 * to render content in the current surface container
 */
window.__quantlab.renderLegacySurface = function(content) {
  const container = document.getElementById('legacy-render-root');
  if (!container) {
    console.warn('[QuantLab React] Legacy render root not found');
    return;
  }
  
  if (typeof content === 'string') {
    container.innerHTML = content;
  } else if (content instanceof HTMLElement) {
    container.innerHTML = '';
    container.appendChild(content);
  } else {
    console.warn('[QuantLab React] Invalid content type for legacy render');
  }
};

/**
 * Surface change handler for legacy/new surface code
 * 
 * Called when user navigates to a different surface
 * Both React and legacy systems can listen for surface changes here
 */
window.__quantlab.onSurfaceChange = function(surface) {
  console.log(`[QuantLab React] Surface changed to: ${surface}`);
  // Legacy code can hook into this to load surface data
  // React surfaces can also use this through props
};

/**
 * Bridge to access current shell state
 */
window.__quantlab.getShellState = function() {
  return {
    reactShell: window.__quantlab.reactShell || null,
    legacyContainer: document.getElementById('legacy-render-root'),
  };
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeReactShell);
} else {
  initializeReactShell();
}

// Export for testing
export { initializeReactShell };
