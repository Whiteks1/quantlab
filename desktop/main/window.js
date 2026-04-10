// @ts-check

const path = require("path");

/**
 * @param {{
 *   BrowserWindow: typeof import("electron").BrowserWindow,
 *   desktopRoot: string,
 *   isSmokeRun: boolean,
 *   onClosed: () => void,
 * }} options
 */
function createMainWindow({ BrowserWindow, desktopRoot, isSmokeRun, onClosed }) {
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

  mainWindow.loadFile(path.join(desktopRoot, "renderer", "index.html"));
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
