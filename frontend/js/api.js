/**
 * api.js — thin fetch wrapper around the backend REST API.
 * All requests go to /api/* — Nginx proxies to the backend container.
 */

const BASE = "/api";

function getToken() {
  return localStorage.getItem("access_token");
}

async function request(method, path, body = null) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const resp = await fetch(`${BASE}${path}`, opts);
  const data = await resp.json().catch(() => ({}));

  if (!resp.ok) {
    const err = new Error(data.error || `HTTP ${resp.status}`);
    err.status = resp.status;
    throw err;
  }
  return data;
}

export const api = {
  // Auth
  register: (email, password) => request("POST", "/auth/register", { email, password }),
  login:    (email, password) => request("POST", "/auth/login", { email, password }),
  logout:   ()               => request("POST", "/auth/logout"),
  me:       ()               => request("GET",  "/auth/me"),

  // Links
  createLink: (original_url, title) => request("POST", "/links", { original_url, title }),
  listLinks:  (page = 1)            => request("GET",  `/links?page=${page}`),
  deleteLink: (short_code)          => request("DELETE", `/links/${short_code}`),

  // Analytics
  analytics: (short_code) => request("GET", `/analytics/${short_code}`),
};
