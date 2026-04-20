import React from 'react';
import { useQuantLab } from './QuantLabContext';
import './TabsBar.css';

/**
 * TabsBar - Workspace tab navigation bar.
 * Replicates the legacy #tabs-bar to support switching between open surfaces.
 */
export function TabsBar() {
  const { state, setActiveTab, closeTab } = useQuantLab();
  const tabs = state.tabs || [];
  const activeTabId = state.activeTabId;

  if (tabs.length === 0) {
    return null;
  }

  return (
    <div id="tabs-bar" className="tabs-bar">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab-pill ${tab.id === activeTabId ? 'is-active' : ''}`}
          onClick={() => setActiveTab(tab.id)}
          type="button"
          data-tab-id={tab.id}
        >
          <span>{tab.title}</span>
          <span
            className="tab-close"
            onClick={(e) => {
              e.stopPropagation();
              closeTab(tab.id);
            }}
            data-close-tab={tab.id}
          >
            ×
          </span>
        </button>
      ))}
    </div>
  );
}
