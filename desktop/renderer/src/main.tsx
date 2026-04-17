import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./globals.css";

const root = document.getElementById("react-root");

if (!root) {
  throw new Error('Missing "#react-root" container.');
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
