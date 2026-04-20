import React, { useState, useMemo } from 'react';
import Topbar from './Topbar.jsx';
import Sidebar from './Sidebar.jsx';
import MainContent from './MainContent.jsx';
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
 * Bridges to the legacy app.js state and provides context to all surfaces.
 */
export default function App() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Build context value that bridges to legacy state
  const contextValue = useQuantLabContextValue();

  React.useEffect(() => {
    if (window.__quantlab) {
      window.__quantlab.rendererMode = 'react';
    }
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

  if (window.__quantlab) {
    window.__quantlab.rendererMode = 'react';
  }

  const handleTabChange = (tabId) => {
    contextValue.setActiveTab(tabId);
  };

  return (
    <QuantLabContextProvider value={contextValue}>
      <div className="app-container">
        <Topbar
          currentSurface={activeTab?.kind}
          onToggleSidebar={handleToggleSidebar}
          isSidebarCollapsed={isSidebarCollapsed}
        />

        <div className="app-main-area">
          <Sidebar
            currentSurface={activeTab?.kind}
            allTabs={allTabs}
            onNavigate={handleTabChange}
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
