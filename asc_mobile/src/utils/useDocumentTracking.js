/**
 * useDocumentTracking.js
 * ──────────────────────
 * Real-time document tracking hook using WebSocket.
 *
 * Usage in DocumentDetailScreen.js:
 *   const { logs, connected } = useDocumentTracking(trackingNumber, token);
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { AppState } from 'react-native';
import { BASE_WS_URL } from '../api/client';

const RECONNECT_DELAY = 3000;  // ms before reconnect attempt

export function useDocumentTracking(trackingNumber, token) {
  const [logs,      setLogs]      = useState([]);
  const [connected, setConnected] = useState(false);
  const [error,     setError]     = useState(null);

  const wsRef          = useRef(null);
  const reconnectTimer = useRef(null);
  const mountedRef     = useRef(true);

  const connect = useCallback(() => {
    if (!trackingNumber || !token) return;

    const url = `${BASE_WS_URL}/ws/docs/${trackingNumber}/?token=${token}`;
    const ws  = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      setConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      try {
        const msg = JSON.parse(event.data);

        if (msg.type === 'history') {
          setLogs(msg.payload);
        } else if (msg.type === 'tracking_update') {
          setLogs(prev => {
            // Avoid duplicates
            const exists = prev.some(l => l.id === msg.payload.id);
            if (exists) return prev;
            return [...prev, msg.payload];
          });
        }
      } catch (e) {
        console.warn('WS parse error:', e);
      }
    };

    ws.onerror = (e) => {
      setError('Connection error');
    };

    ws.onclose = (e) => {
      if (!mountedRef.current) return;
      setConnected(false);
      // Auto-reconnect unless app is in background
      if (AppState.currentState === 'active' && mountedRef.current) {
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
      }
    };
  }, [trackingNumber, token]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    const appStateSub = AppState.addEventListener('change', (state) => {
      if (state === 'active') {
        // Reconnect when app comes back to foreground
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          connect();
        }
      } else {
        // Disconnect when app goes to background to save battery
        wsRef.current?.close();
        clearTimeout(reconnectTimer.current);
      }
    });

    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
      appStateSub.remove();
    };
  }, [connect]);

  return { logs, connected, error };
}
