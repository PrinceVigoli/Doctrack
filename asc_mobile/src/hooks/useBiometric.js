/**
 * useBiometric.js
 * Face ID / fingerprint login for returning users.
 *
 * SECURITY: stores the raw username/password in expo-secure-store (iOS
 * Keychain / Android Keystore-encrypted storage), not AsyncStorage. The
 * previous version stored these in plain AsyncStorage, which is NOT
 * encrypted on either platform — this held the user's actual login
 * password in cleartext on disk.
 */
import { useState, useEffect } from 'react';
import * as LocalAuthentication from 'expo-local-authentication';
import * as secureStorage from '../utils/secureStorage';

const CREDS_KEY = 'doctrack_biometric_creds';

export function useBiometric() {
  const [supported, setSupported] = useState(false);
  const [enrolled,  setEnrolled]  = useState(false);
  const [enabled,   setEnabled]   = useState(false);

  useEffect(() => {
    (async () => {
      const hasHardware = await LocalAuthentication.hasHardwareAsync();
      const isEnrolled  = await LocalAuthentication.isEnrolledAsync();
      const savedCreds  = await secureStorage.getItem(CREDS_KEY);
      setSupported(hasHardware);
      setEnrolled(isEnrolled);
      setEnabled(hasHardware && isEnrolled && !!savedCreds);
    })();
  }, []);

  /** Save credentials after a successful password login */
  const saveCreds = async (username, password) => {
    try {
      await secureStorage.setItem(CREDS_KEY, JSON.stringify({ username, password }));
      setEnabled(true);
    } catch {}
  };

  /** Clear saved credentials (on logout) */
  const clearCreds = async () => {
    await secureStorage.removeItem(CREDS_KEY);
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
      const raw = await secureStorage.getItem(CREDS_KEY);
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
