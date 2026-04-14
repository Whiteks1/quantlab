// @ts-check

/**
 * Transitional desktop renderer bootstrap.
 *
 * React shell work remains deferred until the renderer has real tooling for
 * JSX and bare-package imports. Until then, keep the current desktop
 * operational by booting the proven legacy shell through the existing module
 * entrypoint.
 */

import "./app-legacy.js";

window.__quantlab = window.__quantlab || {};

/**
 * Restore the visible legacy shell while the React renderer tooling is not yet
 * available in the runtime path.
 */
function activateLegacyShell() {
  const reactRoot = document.getElementById("react-root");
  const legacyShell = document.getElementById("legacy-shell");

  if (reactRoot) {
    reactRoot.innerHTML = "";
    reactRoot.setAttribute("hidden", "true");
    reactRoot.style.display = "none";
  }

  if (legacyShell) {
    legacyShell.removeAttribute("hidden");
    legacyShell.classList.remove("hidden");
    legacyShell.style.display = "";
  }

  window.__quantlab.rendererMode = "legacy";
}

window.__quantlab.getShellState = function getShellState() {
  return {
    rendererMode: window.__quantlab.rendererMode || "legacy",
    reactRoot: document.getElementById("react-root"),
    legacyShell: document.getElementById("legacy-shell"),
  };
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", activateLegacyShell, { once: true });
} else {
  activateLegacyShell();
}

export { activateLegacyShell };
