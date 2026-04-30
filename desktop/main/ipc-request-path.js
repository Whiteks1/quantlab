// @ts-check

/**
 * Pure helpers for validating and classifying relative IPC paths that the
 * renderer is allowed to ask the main process to forward to the local
 * research_ui server.
 *
 * These helpers were previously inlined in `register-ipc.js`. They are
 * extracted here so the IPC path-validation policy is:
 *   - observable (importable and unit-testable in isolation),
 *   - single-source (no duplication across handlers),
 *   - side-effect-free (no logging, no I/O, no state).
 *
 * Behavior-preserving: same logic and same error messages as before.
 */

/**
 * Normalize a relative path received from the renderer over IPC.
 *
 * Rejects:
 *   - empty / whitespace-only values
 *   - absolute URLs (anything starting with a scheme like "http:", "file:", "ftp:")
 *   - values that do not start with "/"
 *
 * Strips the query string and fragment from the returned path.
 *
 * @param {unknown} relativePath
 * @returns {string} the normalized path, guaranteed to start with "/" and to
 *   contain no "?" or "#".
 * @throws {Error} when the input is empty, is an absolute URL, or is missing
 *   the leading "/".
 */
function normalizeRelativePath(relativePath) {
  const value = String(relativePath || "").trim();
  if (!value) {
    throw new Error("Relative path is required.");
  }
  if (/^[a-zA-Z][a-zA-Z\d+\-.]*:/.test(value)) {
    throw new Error("Absolute URLs are not allowed.");
  }
  if (!value.startsWith("/")) {
    throw new Error("Relative path must start with '/'.");
  }
  return value.split("?", 1)[0].split("#", 1)[0];
}

/**
 * Return true when the given (already normalized) path targets a research_ui
 * POST endpoint that must be gated with the local API token.
 *
 * The set is intentionally small and closed. To add a new sensitive endpoint,
 * extend this function and its tests deliberately.
 *
 * @param {string} normalizedPath
 * @returns {boolean}
 */
function isSensitiveResearchUiPostPath(normalizedPath) {
  return (
    normalizedPath === "/api/launch-control" ||
    normalizedPath === "/api/stepbit-workspace/start"
  );
}

module.exports = {
  normalizeRelativePath,
  isSensitiveResearchUiPostPath,
};
