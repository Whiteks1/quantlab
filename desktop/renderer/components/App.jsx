import React, { useState } from 'react';
import Topbar from './Topbar.jsx';
import Sidebar from './Sidebar.jsx';
import MainContent from './MainContent.jsx';
import {
  QuantLabContextProvider,
  useQuantLabContextValue,
  RegistryProvider,
} from './QuantLabContext.jsx';

/**
 * AppShell — inner shell component.
 * Lives inside RegistryProvider so useQuantLabContextValue can call useRegistry().
 */
function AppShell() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Build the full context value (must be called unconditionally before any early return)
  const contextValue = useQuantLabContextValue();

  React.useEffect(() => {
    if (!window.__quantlab) {
      window.__quantlab = { rendererMode: 'react' };
    } else {
      window.__quantlab.rendererMode = 'react';
    }
    window.__quantlab.getShellState = () => ({
      rendererMode: 'react',
      reactRoot: document.getElementById('react-root'),
      legacyShell: document.getElementById('legacy-shell'),
      currentSurface: window.__quantlab?.currentSurface || 'runs',
    });
  }, []);

  const activeTab = contextValue.state?.tabs?.find(
    (t) => t.id === contextValue.state.activeTabId
  ) || null;
  const allTabs = contextValue.state?.tabs || [];
  const currentSurface = activeTab?.navKind || activeTab?.kind || 'system';

  // Expose metadata for smoke tests; kept in an effect to avoid conditional hook calls
  React.useEffect(() => {
    if (!window.__quantlab) return;
    window.__quantlab.currentSurface = currentSurface;
  }, [currentSurface]);

  // Loading guard — safe here because all hooks have already been called
  if (!contextValue?.state || !contextValue.state.isInitialized) {
    return (
      <div className="app-container loading">
        <div className="loading-message">
          <div className="spinner"></div>
          <p>QuantLab Desktop is initializing...</p>
        </div>
      </div>
    );
  }

  const handleToggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const handleTabChange = (tabId) => {
    contextValue.setActiveTab(tabId);
  };

  return (
    <QuantLabContextProvider value={contextValue}>
      <div className="app-container">
        <Topbar
          currentSurface={currentSurface}
          onToggleSidebar={handleToggleSidebar}
          isSidebarCollapsed={isSidebarCollapsed}
        />

        <div className="app-main-area">
          <Sidebar
            currentSurface={currentSurface}
            isCollapsed={isSidebarCollapsed}
          />

          <MainContent
            activeTab={activeTab}
            allTabs={allTabs}
            onTabChange={handleTabChange}
          />
        </div>
      </div>
    </QuantLabContextProvider>
  );
}

/**
 * App - Root component for the QuantLab Desktop React shell.
 *
 * Mounts the RegistryProvider (native data authority) as the outermost
 * wrapper so that all hooks downstream can consume registry state.
 */
export default function App() {
  return (
    <RegistryProvider>
      <AppShell />
    </RegistryProvider>
  );
}
