import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('finnk_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('finnk_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      if (token) {
        try {
          const profile = await api.auth.getProfile();
          setUser(profile);
          localStorage.setItem('finnk_user', JSON.stringify(profile));
        } catch (err) {
          logout();
        }
      }
      setLoading(false);
    }

    loadUser();

    const handleUnauthorized = () => logout();
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, [token]);

  const login = async (email, password) => {
    const res = await api.auth.login({ email, password });
    setToken(res.access_token);
    setUser(res.user);
    localStorage.setItem('finnk_token', res.access_token);
    localStorage.setItem('finnk_user', JSON.stringify(res.user));
    return res;
  };

  const register = async (name, email, password) => {
    const res = await api.auth.register({ name, email, password });
    setToken(res.access_token);
    setUser(res.user);
    localStorage.setItem('finnk_token', res.access_token);
    localStorage.setItem('finnk_user', JSON.stringify(res.user));
    return res;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('finnk_token');
    localStorage.removeItem('finnk_user');
  };

  const updateProfile = async (data) => {
    const updated = await api.auth.updateProfile(data);
    setUser(updated);
    localStorage.setItem('finnk_user', JSON.stringify(updated));
    return updated;
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
