/**
 * monitoring.js — Grafana Faro RUM initialisation.
 *
 * Loaded as the FIRST script on every page so all user interactions,
 * page loads, JS errors and web vitals are captured from the start.
 *
 * Faro ships telemetry to Grafana Alloy which forwards to Loki (logs)
 * and Tempo (traces). The collector URL is injected via window.ENV at
 * runtime by Nginx sub_filter or a tiny inline <script>.
 */

// Faro is loaded from CDN in the HTML <head> as a classic script.
// This module references the global after the CDN script has run.

function initFaro() {
  const collectorUrl =
    (window.ENV && window.ENV.FARO_URL) ||
    "http://localhost:12347/collect";

  if (!window.GrafanaFaro) {
    console.warn("[monitoring] Grafana Faro SDK not loaded — skipping RUM init.");
    return;
  }

  const { initializeFaro, getWebInstrumentations } = window.GrafanaFaro;

  window.faro = initializeFaro({
    url: collectorUrl,
    app: {
      name: "url-shortener-frontend",
      version: "0.1.0",
      environment: window.ENV?.APP_ENV || "production",
    },
    instrumentations: [
      ...getWebInstrumentations({
        captureConsole: true,
        captureConsoleDisabledLevels: ["debug"],
      }),
    ],
  });

  console.info("[monitoring] Faro RUM initialised →", collectorUrl);
}

// Run after DOM content (Faro CDN script must be in <head> before this)
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initFaro);
} else {
  initFaro();
}

/**
 * Push a custom event to Faro (call from other modules).
 * @param {string} name - event name, e.g. "link_created"
 * @param {Record<string, string>} attributes - string key-value pairs
 */
export function trackEvent(name, attributes = {}) {
  try {
    window.faro?.api?.pushEvent(name, attributes);
  } catch (err) {
    console.warn("[monitoring] trackEvent failed:", err);
  }
}

/**
 * Push an error to Faro manually (for caught errors you still want tracked).
 * @param {Error} error
 */
export function trackError(error) {
  try {
    window.faro?.api?.pushError(error);
  } catch (err) {
    console.warn("[monitoring] trackError failed:", err);
  }
}
