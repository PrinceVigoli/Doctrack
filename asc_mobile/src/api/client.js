/**
 * API client configuration.
 *
 * Development (LAN/VPS): set HOST and PORT to your backend server address.
 * Production:            uncomment the HTTPS/WSS block below and delete the
 *                        HTTP block above it.
 */
import axios from 'axios';
import * as secureStorage from '../utils/secureStorage';

// ── Development ───────────────────────────────────────────────────────────────
const HOST = '192.168.1.7';  // ← your VPS IP or LAN address
const PORT = '8000';
export const BASE_URL    = `http://${HOST}:${PORT}/api`;
export const BASE_HOST   = `http://${HOST}:${PORT}`;   // bare host, used for file preview URLs
export const BASE_WS_URL = `ws://${HOST}:${PORT}`;     // WebSocket base

// ── Production (uncomment + delete the Development block above) ───────────────
// export const BASE_URL    = 'https://yourdomain.com/api';
// export const BASE_HOST   = 'https://yourdomain.com';
// export const BASE_WS_URL = 'wss://yourdomain.com';

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
});

// Attach the access token to every outgoing request, if we have one.
client.interceptors.request.use(async (config) => {
  const token = await secureStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On a 401, try to refresh the access token once and replay the original
// request. If refresh also fails, clear stored tokens and let the error
// propagate (AuthContext / screens handle redirecting to login).
let refreshPromise = null;

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const status    = error.response?.status;

    if (status === 401 && !original?._retry && !original?.url?.includes('/auth/login/')) {
      original._retry = true;
      try {
        const refresh = await secureStorage.getItem('refresh_token');
        if (!refresh) throw error;

        if (!refreshPromise) {
          refreshPromise = axios
            .post(`${BASE_URL}/auth/refresh/`, { refresh })
            .finally(() => { refreshPromise = null; });
        }
        const { data } = await refreshPromise;
        await secureStorage.setItem('access_token', data.access);

        original.headers = original.headers || {};
        original.headers.Authorization = `Bearer ${data.access}`;
        return client(original);
      } catch (refreshErr) {
        await secureStorage.multiRemove(['access_token', 'refresh_token']);
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export default client;
