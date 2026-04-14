import type { QuantlabDesktopBridge } from "../shared/ipc/bridge";

interface QuantLabShellState {
  rendererMode?: "legacy" | "react";
  currentSurface?: string;
  onNavigate?: (surface: string) => void;
  legacyContainer?: HTMLElement | null;
  reactRoot?: HTMLElement | null;
  legacyShell?: HTMLElement | null;
  reactShell?: any;
}

interface QuantLabGlobal {
  renderLegacySurface?: (content: string | HTMLElement) => void;
  onSurfaceChange?: (surface: string) => void;
  getShellState?: () => QuantLabShellState;
  legacyContentContainer?: HTMLElement | null;
  rendererMode?: "legacy" | "react";
  reactShell?: QuantLabShellState;
}

declare global {
  interface Window {
    quantlabDesktop: QuantlabDesktopBridge;
    __quantlab?: QuantLabGlobal;
  }
}

export {};

