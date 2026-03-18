import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./theme/global.css";

// Initialize Telegram WebApp BEFORE React mounts
const tgApp = window.Telegram?.WebApp;
if (tgApp) {
  tgApp.ready();
  tgApp.expand();
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
