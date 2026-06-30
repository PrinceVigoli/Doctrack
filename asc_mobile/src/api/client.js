/**
 * API client configuration.
 *
 * Development (LAN/VPS): set HOST and PORT to your backend server address.
 * Production:            uncomment the HTTPS/WSS block below and delete the
 *                        HTTP block above it.
 */

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
