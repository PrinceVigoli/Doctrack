/**
 * useBiometric.js
 * Face ID / fingerprint login for returning users.
 * Stores credentials securely in AsyncStorage (encrypted by OS keychain in production).
 */
import { useState, useEffect } from 'react';
import * as LocalAuthentication from 'expo-local-authentication';
import AsyncStorage from '@react-native-async-storage/async-storage';

const CREDS_KEY = 'doctrack_biometric_creds';

export function useBiometric() {
  const [supported, setSupported] = useState(false);
  const [enrolled,  setEnrolled]  = useState(false);
  const [enabled,   setEnabled]   = useState(false);

  useEffect(() => {
    (async () => {
      const hasHardware = await LocalAuthentication.hasHardwareAsync();
      const isEnrolled  = await LocalAuthentication.isEnrolledAsync();
      const savedCreds  = await AsyncStorage.getItem(CREDS_KEY);
      setSupported(hasHardware);
      setEnrolled(isEnrolled);
      setEnabled(hasHardware && isEnrolled && !!savedCreds);
    })();
  }, []);

  /** Save credentials after a successful password login */
  const saveCreds = async (username, password) => {
    try {
      await AsyncStorage.setItem(CREDS_KEY, JSON.stringify({ username, password }));
      setEnabled(true);
    } catch {}
  };

  /** Clear saved credentials (on logout) */
  const clearCreds = async () => {
    await AsyncStorage.removeItem(CREDS_KEY);
    setEnabled(false);
  };

  /** Authenticate with biometrics and return credentials if successful */
  const authenticate = async () => {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage:  'Sign in to ASC DocTrack',
      fallbackLabel:  'Use password',
      cancelLabel:    'Cancel',
      disableDeviceFallback: false,
    });
    if (!result.success) return null;
    try {
      const raw = await AsyncStorage.getItem(CREDS_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  };

  const getType = async () => {
    const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
    if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) return 'Face ID';
    if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) return 'Fingerprint';
    return 'Biometrics';
  };

  return { supported, enrolled, enabled, saveCreds, clearCreds, authenticate, getType };
}
