import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('finnk_user');
    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem('finnk_token'));
  // Não bloqueia a interface se já possuir dados válidos em cache
  const [loading, setLoading] = useState(() => {
    const saved = localStorage.getItem('finnk_user');
    const savedToken = localStorage.getItem('finnk_token');
    return !(saved && savedToken);
  });

  useEffect(() => {
    let isMounted = true;
    async function initAuth() {
      const savedToken = localStorage.getItem('finnk_token');
      if (savedToken) {
        try {
          const profile = await api.auth.getProfile();
          if (isMounted) {
            setUser(profile);
            localStorage.setItem('finnk_user', JSON.stringify(profile));
          }
        } catch (err) {
          if (isMounted) logout();
        }
      }
      if (isMounted) setLoading(false);
    }

    initAuth();

    const handleUnauthorized = () => logout();
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => {
      isMounted = false;
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, []);

  const login = async (email, password) => {
    const res = await api.auth.login({ email, password });
    localStorage.setItem('finnk_token', res.access_token);
    localStorage.setItem('finnk_user', JSON.stringify(res.user));
    setToken(res.access_token);
    setUser(res.user);
    setLoading(false);
    return res;
  };

  const register = async (name, email, password) => {
    const res = await api.auth.register({ name, email, password });
    localStorage.setItem('finnk_token', res.access_token);
    localStorage.setItem('finnk_user', JSON.stringify(res.user));
    setToken(res.access_token);
    setUser(res.user);
    setLoading(false);
    return res;
  };

  const loginGoogle = async (googleUser) => {
    const res = await api.auth.googleLogin({
      id_token: googleUser.idToken,
      email: googleUser.email,
      name: googleUser.name,
      photo_url: googleUser.photoUrl
    });
    localStorage.setItem('finnk_token', res.access_token);
    localStorage.setItem('finnk_user', JSON.stringify(res.user));
    setToken(res.access_token);
    setUser(res.user);
    setLoading(false);
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
    <AuthContext.Provider value={{ user, token, loading, login, register, loginGoogle, logout, updateProfile }}>
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
