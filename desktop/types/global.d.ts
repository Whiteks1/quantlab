import type { QuantlabDesktopBridge } from "../shared/ipc/bridge";

interface QuantLabShellState {
  currentSurface?: string;
  onNavigate?: (surface: string) => void;
  legacyContainer?: HTMLElement | null;
  reactShell?: any;
}

interface QuantLabGlobal {
  renderLegacySurface?: (content: string | HTMLElement) => void;
  onSurfaceChange?: (surface: string) => void;
  getShellState?: () => QuantLabShellState;
  legacyContentContainer?: HTMLElement | null;
  reactShell?: QuantLabShellState;
}

declare global {
  interface Window {
    quantlabDesktop: QuantlabDesktopBridge;
    __quantlab?: QuantLabGlobal;
  }
}

export {};

