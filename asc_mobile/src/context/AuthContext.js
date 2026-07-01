import React, { createContext, useContext, useState, useEffect } from 'react';
import * as secureStorage from '../utils/secureStorage';
import { authAPI } from '../api/services';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user,    setUser]    = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore session on app launch
  useEffect(() => {
    (async () => {
      try {
        const token = await secureStorage.getItem('access_token');
        if (token) {
          const { data } = await authAPI.me();
          setUser(data);
        }
      } catch {
        await secureStorage.multiRemove(['access_token', 'refresh_token']);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = async (username, password) => {
    const { data } = await authAPI.login(username, password);
    await secureStorage.setItem('access_token',  data.access);
    await secureStorage.setItem('refresh_token', data.refresh);
    const me = await authAPI.me();
    setUser(me.data);
    return me.data;
  };

  const logout = async () => {
    try {
      const refresh = await secureStorage.getItem('refresh_token');
      if (refresh) await authAPI.logout(refresh);
    } catch {}
    await secureStorage.multiRemove(['access_token', 'refresh_token']);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
