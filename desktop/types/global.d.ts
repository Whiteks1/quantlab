import type { QuantlabDesktopBridge } from "../shared/ipc/bridge";

declare global {
  interface Window {
    quantlabDesktop: QuantlabDesktopBridge;
  }
}

export {};
