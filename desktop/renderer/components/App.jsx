import React, { useState } from 'react';
import Topbar from './Topbar.jsx';
import Sidebar from './Sidebar.jsx';
import MainContent from './MainContent';
import {
  QuantLabContextProvider,
  useQuantLabContextValue,
} from './QuantLabContext.jsx';

/**
 * App - Root component for the QuantLab Desktop React shell
 * 
 * Manages the overall layout and state for:
 * - Topbar with runtime status
 * - Sidebar with navigation
 * - MainContent area for surfaces (Runs, Compare, Candidates)
 * 
 * Provides React-owned state through the preload bridge without app-legacy.js.
 */
export default function App() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Build context value owned by the React runtime.
  const contextValue = useQuantLabContextValue();

  React.useEffect(() => {
    window.__quantlab = window.__quantlab || {};
    window.__quantlab.rendererMode = 'react';
    window.__quantlab.reactShell = {
      rendererMode: 'react',
      reactRoot: document.getElementById('react-root'),
    };
    window.__quantlab.getShellState = () => ({
      rendererMode: 'react',
      reactRoot: document.getElementById('react-root'),
      currentSurface: window.__quantlab?.reactShell?.currentSurface || 'runs',
    });
  }, []);

  if (!contextValue?.state) {
    return (
      <div className="app-container loading">
        <div className="loading-message">
          <p>QuantLab Desktop is initializing...</p>
        </div>
      </div>
    );
  }

  const handleToggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  // Get active tab from state
  const activeTab = contextValue.state?.tabs?.find(
    (t) => t.id === contextValue.state.activeTabId
  ) || null;

  const allTabs = contextValue.state?.tabs || [];

  const currentSurface = activeTab?.navKind || activeTab?.kind || 'system';

  if (window.__quantlab?.reactShell) {
    window.__quantlab.reactShell.currentSurface = currentSurface;
  }

  const handleTabChange = (tabId) => {
    contextValue.setActiveTab(tabId);
  };

  const handleNavigate = (tab) => {
    contextValue.openTab(tab);
  };

  return (
    <QuantLabContextProvider value={contextValue}>
      <div className="app-container" data-renderer-mode="react" data-smoke="react-shell">
        <Topbar
          currentSurface={currentSurface}
          onToggleSidebar={handleToggleSidebar}
          isSidebarCollapsed={isSidebarCollapsed}
        />

        <div className="app-main-area">
          <Sidebar
            currentSurface={currentSurface}
            allTabs={allTabs}
            onNavigate={handleNavigate}
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
