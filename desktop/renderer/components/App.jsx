import React, { useState } from 'react';
import Topbar from './Topbar.jsx';
import Sidebar from './Sidebar.jsx';
import MainContent from './MainContent.jsx';

/**
 * @typedef {{
 *   currentSurface: string;
 *   isSidebarCollapsed: boolean;
 * }} AppState
 */

/**
 * App - Root component for the QuantLab Desktop React shell
 * 
 * Manages the overall layout and state for:
 * - Topbar with runtime status
 * - Sidebar with navigation
 * - MainContent area for surfaces
 * 
 * Does NOT migrate existing surfaces yet; provides routing foundation only.
 */
export default function App() {
  // Start with System surface as default
  const [currentSurface, setCurrentSurface] = useState('system');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  const handleNavigate = (surface) => {
    setCurrentSurface(surface);
  };

  const handleToggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  return (
    <div className="app-container">
      <Topbar 
        currentSurface={currentSurface}
        onToggleSidebar={handleToggleSidebar}
        isSidebarCollapsed={isSidebarCollapsed}
      />
      
      <div className="app-main-area">
        <Sidebar
          currentSurface={currentSurface}
          onNavigate={handleNavigate}
          isCollapsed={isSidebarCollapsed}
        />
        
        <MainContent
          currentSurface={currentSurface}
          onNavigate={handleNavigate}
        />
      </div>
    </div>
  );
}
