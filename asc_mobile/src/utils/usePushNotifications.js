/**
 * src/utils/usePushNotifications.js
 * ─────────────────────────────────────────────────────────────
 * Registers the device for Expo Push Notifications and sends
 * the token to the Django backend.
 *
 * Usage:
 *   import { usePushNotifications } from '../utils/usePushNotifications';
 *   // call inside a screen after login:
 *   usePushNotifications();
 */
import { useEffect, useRef } from 'react';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform, Alert } from 'react-native';
import client from '../api/client';

// How to handle notifications when app is in foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge:  true,
  }),
});

export function usePushNotifications(navigation) {
  const notificationListener = useRef();
  const responseListener     = useRef();

  useEffect(() => {
    registerForPushNotifications();

    // Foreground notification received
    notificationListener.current = Notifications.addNotificationReceivedListener(notification => {
      console.log('Notification received:', notification);
    });

    // User tapped on a notification
    responseListener.current = Notifications.addNotificationResponseReceivedListener(response => {
      const data = response.notification.request.content.data;
      // Navigate to the relevant document if we have its ID
      if (data?.document_id && navigation) {
        navigation.navigate('DocumentDetail', { id: data.document_id });
      }
    });

    return () => {
      Notifications.removeNotificationSubscription(notificationListener.current);
      Notifications.removeNotificationSubscription(responseListener.current);
    };
  }, []);
}

async function registerForPushNotifications() {
  // Push notifications only work on real devices
  if (!Device.isDevice) {
    console.log('Push notifications require a physical device.');
    return;
  }

  // Request permission
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    Alert.alert(
      'Notifications Disabled',
      'Enable notifications in your phone settings to receive document updates.',
    );
    return;
  }

  // Android needs a notification channel
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('doctrack', {
      name:            'DocTrack Alerts',
      importance:      Notifications.AndroidImportance.HIGH,
      vibrationPattern:[0, 250, 250, 250],
      lightColor:      '#1B4332',
      sound:           'default',
    });
  }

  // Get Expo push token
  try {
    const tokenData = await Notifications.getExpoPushTokenAsync({
      projectId: 'asc-doctrack', // must match app.json expo.slug
    });
    const token = tokenData.data;
    console.log('Expo push token:', token);

    // Register token with Django backend
    await client.post('/notifications/register/', {
      token,
      platform:    'expo',
      device_name: Device.deviceName || 'Unknown Device',
    });
    console.log('Push token registered with server.');
  } catch (err) {
    console.warn('Push token registration failed:', err.message);
  }
}

/**
 * Call this on logout to deregister the device token.
 */
export async function deregisterPushToken() {
  try {
    const tokenData = await Notifications.getExpoPushTokenAsync({
      projectId: 'asc-doctrack',
    });
    await client.post('/notifications/deregister/', { token: tokenData.data });
  } catch {}
}
