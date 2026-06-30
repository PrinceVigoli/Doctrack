/* api.js — all calls to Django backend
 *
 * Development: set BACKEND_ORIGIN to your server's IP/domain.
 * Production:  when the admin panel is served from the same origin as the
 *              backend (e.g. nginx proxying /api), leave BACKEND_ORIGIN as ''
 *              so all requests use relative paths and CORS is not needed.
 *
 * Examples:
 *   const BACKEND_ORIGIN = '';                        // same-origin (production)
 *   const BACKEND_ORIGIN = 'http://192.168.1.7:8000'; // LAN dev server
 *   const BACKEND_ORIGIN = 'https://yourdomain.com';  // production VPS
 */
const BACKEND_ORIGIN = 'http://127.0.0.1:8000'; // ← change this before deploying
const BASE_URL = BACKEND_ORIGIN + '/api';

async function apiFetch(path, opts = {}) {
  const token = localStorage.getItem('access_token');
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res = await fetch(BASE_URL + path, { ...opts, headers });

  // Try token refresh on 401
  if (res.status === 401) {
    const refresh = localStorage.getItem('refresh_token');
    if (refresh) {
      const r = await fetch(BASE_URL + '/auth/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
      if (r.ok) {
        const d = await r.json();
        localStorage.setItem('access_token', d.access);
        headers['Authorization'] = `Bearer ${d.access}`;
        res = await fetch(BASE_URL + path, { ...opts, headers });
      } else {
        Auth.logout(); return;
      }
    }
  }

  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const d = await res.json(); msg = d.detail || JSON.stringify(d); } catch {}
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
}

const API = {
  // Auth
  login:    (u, p) => apiFetch('/auth/login/', { method:'POST', body: JSON.stringify({ username:u, password:p }) }),
  me:       ()     => apiFetch('/auth/me/'),
  offices:  (p={}) => apiFetch('/auth/offices/?' + new URLSearchParams(p)),
  users:    (p={}) => apiFetch('/auth/users/?'   + new URLSearchParams(p)),
  register: (d)    => apiFetch('/auth/register/', { method:'POST', body: JSON.stringify(d) }),

  // Documents
  docs:       (p={})   => apiFetch('/docs/?' + new URLSearchParams(p)),
  doc:        (id)     => apiFetch(`/docs/${id}/`),
  docForward: (id, to, note) => apiFetch(`/docs/${id}/forward/`,       { method:'POST', body: JSON.stringify({ to_office_id: to, note }) }),
  docStatus:  (id, s, note)  => apiFetch(`/docs/${id}/update-status/`, { method:'POST', body: JSON.stringify({ status: s, note }) }),
  docTypes:   ()       => apiFetch('/docs/types/'),

  // Dashboard
  summary:  () => apiFetch('/dashboard/summary/'),
  activity: () => apiFetch('/dashboard/activity/'),
};
