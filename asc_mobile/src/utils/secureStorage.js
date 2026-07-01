/**
 * secureStorage.js
 * ─────────────────
 * SECURITY: wrapper around expo-secure-store, used for anything sensitive
 * (JWTs, saved login credentials). On iOS this is backed by the Keychain;
 * on Android by Keystore-encrypted SharedPreferences — unlike AsyncStorage,
 * which is plain unencrypted storage on both platforms.
 *
 * Do NOT use this for non-sensitive data (e.g. cached document lists) —
 * SecureStore has tighter size limits than AsyncStorage and there's no
 * benefit to encrypting data that isn't sensitive. Keep using AsyncStorage
 * (see useOffline.js) for that.
 *
 * API mirrors the subset of AsyncStorage this app actually uses, so call
 * sites don't need to learn a new shape.
 */
import * as SecureStore from 'expo-secure-store';

export async function getItem(key) {
  try {
    return await SecureStore.getItemAsync(key);
  } catch {
    return null;
  }
}

export async function setItem(key, value) {
  await SecureStore.setItemAsync(key, value);
}

export async function removeItem(key) {
  try {
    await SecureStore.deleteItemAsync(key);
  } catch {
    // Nothing stored under this key — fine to ignore.
  }
}

export async function multiRemove(keys) {
  await Promise.all(keys.map(removeItem));
}
