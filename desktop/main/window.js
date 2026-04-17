// @ts-check

const path = require("path");
const fs = require("fs");

/**
 * @param {{
 *   BrowserWindow: typeof import("electron").BrowserWindow,
 *   desktopRoot: string,
 *   isSmokeRun: boolean,
 *   onClosed: () => void,
 * }} options
 */
function createMainWindow({ BrowserWindow, desktopRoot, isSmokeRun, onClosed }) {
  const useReactRenderer = process.env.QUANTLAB_DESKTOP_RENDERER === "react";
  const mainWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1100,
    minHeight: 760,
    show: !isSmokeRun,
    autoHideMenuBar: true,
    backgroundColor: "#0b1118",
    title: "QuantLab Desktop",
    webPreferences: {
      preload: path.join(desktopRoot, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  if (useReactRenderer && process.env.NODE_ENV === "development") {
    mainWindow.loadURL("http://127.0.0.1:5173");
  } else {
    const distEntry = path.join(desktopRoot, "renderer", "dist", "index.html");
    const sourceEntry = path.join(desktopRoot, "renderer", "index.html");
    const legacyEntry = path.join(desktopRoot, "renderer", "legacy.html");
    const entry = useReactRenderer
      ? (fs.existsSync(distEntry) ? distEntry : sourceEntry)
      : legacyEntry;
    mainWindow.loadFile(entry);
  }
  if (!isSmokeRun) {
    mainWindow.once("ready-to-show", () => {
      if (!mainWindow || mainWindow.isDestroyed()) return;
      mainWindow.show();
    });
  }
  mainWindow.on("closed", () => {
    onClosed();
  });

  return mainWindow;
}

module.exports = { createMainWindow };
