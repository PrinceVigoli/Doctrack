/**
 * useOffline.js
 * Caches last-fetched document list in AsyncStorage.
 * Returns { isOnline, cachedDocs, saveCache }
 */
import { useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const CACHE_KEY = 'doctrack_docs_cache';
const CACHE_TTL = 24 * 60 * 60 * 1000; // 24 hours

export function useOffline() {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    // Simple online check via fetch
    const check = async () => {
      try {
        const r = await fetch('https://www.google.com', { method: 'HEAD', timeout: 3000 });
        setIsOnline(r.ok);
      } catch {
        setIsOnline(false);
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  const saveCache = async (docs) => {
    try {
      await AsyncStorage.setItem(CACHE_KEY, JSON.stringify({ docs, ts: Date.now() }));
    } catch {}
  };

  const loadCache = async () => {
    try {
      const raw = await AsyncStorage.getItem(CACHE_KEY);
      if (!raw) return [];
      const { docs, ts } = JSON.parse(raw);
      if (Date.now() - ts > CACHE_TTL) return [];
      return docs;
    } catch { return []; }
  };

  return { isOnline, saveCache, loadCache };
}
