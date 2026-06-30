/**
 * useNotifications.js
 * ────────────────────
 * Handles both:
 *   1. Real-time in-app notifications via WebSocket
 *   2. Expo push notification registration
 *
 * Usage in App.js (wrap once at root level):
 *   useNotifications(accessToken);
 */
import { useEffect, useRef, useCallback } from 'react';
import { AppState, Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { BASE_WS_URL } from '../api/client';
import { registerPushToken } from '../api/services';

// Configure how notifications appear when app is in foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge:  true,
  }),
});

export function useNotifications(token, onNotification) {
  const wsRef          = useRef(null);
  const reconnectTimer = useRef(null);
  const mountedRef     = useRef(true);

  // ── Register Expo push token ──────────────────────────────────────────────
  const registerForPushNotifications = useCallback(async () => {
    if (!Device.isDevice) return;  // only on real devices

    const { status: existing } = await Notifications.getPermissionsAsync();
    let finalStatus = existing;

    if (existing !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') return;

    // Android notification channel
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('doctrack', {
        name:       'DocTrack Notifications',
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#1B4332',
      });
    }

    const pushToken = await Notifications.getExpoPushTokenAsync();
    if (pushToken?.data && token) {
      await registerPushToken({
        token:    pushToken.data,
        platform: 'expo',
      }).catch(e => console.warn('Push token registration failed:', e));
    }
  }, [token]);

  // ── WebSocket for in-app real-time notifications ──────────────────────────
  const connectWebSocket = useCallback(() => {
    if (!token) return;

    const url = `${BASE_WS_URL}/ws/notifications/?token=${token}`;
    const ws  = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'notification' && onNotification) {
          onNotification(msg);
        }
      } catch (e) {
        console.warn('Notification WS parse error:', e);
      }
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      if (AppState.currentState === 'active') {
        reconnectTimer.current = setTimeout(connectWebSocket, 4000);
      }
    };
  }, [token, onNotification]);

  useEffect(() => {
    mountedRef.current = true;

    registerForPushNotifications();
    connectWebSocket();

    // Handle notification taps (when app is backgrounded)
    const tapSub = Notifications.addNotificationResponseReceivedListener(response => {
      const data = response.notification.request.content.data;
      if (onNotification && data) {
        onNotification({ ...data, type: 'notification_tap' });
      }
    });

    const appStateSub = AppState.addEventListener('change', state => {
      if (state === 'active') {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          connectWebSocket();
        }
      } else {
        wsRef.current?.close();
        clearTimeout(reconnectTimer.current);
      }
    });

    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
      tapSub.remove();
      appStateSub.remove();
    };
  }, [connectWebSocket, registerForPushNotifications]);
}
