/**
 * auth.js — authentication state + helpers used by all pages.
 */

export function saveToken(token) {
  localStorage.setItem("access_token", token);
}

export function getToken() {
  return localStorage.getItem("access_token");
}

export function clearToken() {
  localStorage.removeItem("access_token");
}

export function isLoggedIn() {
  return Boolean(getToken());
}

/**
 * Redirect to login if not authenticated.
 * Call at the top of every protected page.
 */
export function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = "/pages/login";
  }
}

/**
 * Redirect to dashboard if already authenticated.
 * Call at the top of login/register pages.
 */
export function requireGuest() {
  if (isLoggedIn()) {
    window.location.href = "/pages/dashboard";
  }
}
